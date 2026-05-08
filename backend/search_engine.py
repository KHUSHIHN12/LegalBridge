import math
import re
import string
from dataclasses import dataclass
from typing import Dict, Iterable, List

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SECTION_PATTERN = re.compile(r"\b(?:ipc|bns|section|sec\.?)?\s*([0-9]{1,4}[a-zA-Z]?)\b")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


LEGAL_STOPWORDS = {
    "accused",
    "another",
    "case",
    "complaint",
    "husband",
    "person",
    "section",
    "someone",
    "victim",
    "wife",
}

STOPWORDS = set(ENGLISH_STOP_WORDS).union(LEGAL_STOPWORDS)


QUERY_EXPANSIONS = {
    "anonymous": ["unknown", "concealed", "secret"],
    "assault": ["attack", "force", "hurt", "injury"],
    "abuse": ["assault", "force", "rape", "modesty", "outrage"],
    "abused": ["assault", "force", "rape", "modesty", "outrage"],
    "beat": ["hurt", "assault", "injury"],
    "burn": ["fire", "flame", "bodily", "death"],
    "call": ["communication", "message", "threat"],
    "dowry": ["marriage", "cruelty", "husband", "wife"],
    "fake": ["false", "forged", "fraudulent", "deception"],
    "fraud": ["cheating", "dishonestly", "deception"],
    "investment": ["property", "money", "entrustment", "scheme"],
    "kill": ["death", "murder", "culpable", "homicide"],
    "killed": ["death", "murder", "culpable", "homicide"],
    "money": ["property", "valuable", "dishonestly"],
    "robbery": ["theft", "extortion", "hurt", "force"],
    "scheme": ["cheating", "deception", "fraud"],
    "sexual": ["rape", "modesty", "woman", "assault"],
    "sexually": ["rape", "modesty", "woman", "assault"],
    "stole": ["theft", "dishonestly", "property"],
    "threatened": ["criminal", "intimidation", "alarm"],
    "wife": ["woman", "marriage", "husband", "cruelty"],
}


HIGH_INTENT_TERMS = {
    "acid",
    "anonymous",
    "anonymou",
    "cheat",
    "cheating",
    "counterfeit",
    "cruelty",
    "death",
    "dowry",
    "extortion",
    "forgery",
    "homicide",
    "intimidation",
    "kidnap",
    "mischief",
    "modesty",
    "murder",
    "rape",
    "robbery",
    "sexual",
    "theft",
}

LOW_COMPLAINT_VALUE_TITLES = {
    "act",
    "gender",
    "government",
    "india",
    "judge",
    "man woman",
    "number",
    "person",
    "public",
}


@dataclass(frozen=True)
class LegalDocument:
    law: str
    section: str
    title: str
    description: str
    search_text: str
    title_text: str


class LegalSearchEngine:
    """Lightweight semantic legal section search backed by TF-IDF."""

    def __init__(self, ipc_sections: Dict, bns_sections: Dict):
        self.documents = self._build_documents(ipc_sections, bns_sections)
        self.vectorizer = TfidfVectorizer(
            analyzer=self._analyze,
            min_df=1,
            sublinear_tf=True,
            norm="l2",
        )
        self.document_matrix = self.vectorizer.fit_transform(
            [document.search_text for document in self.documents]
        )

    def search(
        self,
        query: str,
        law: str = "all",
        limit: int = 20,
        min_score: float = 0.0,
    ) -> List[Dict]:
        query = (query or "").strip()
        law = (law or "all").strip().lower()

        allowed_laws = self._allowed_laws(law)
        if not query:
            return [
                self._to_result(document, 0.0)
                for document in self.documents
                if document.law.lower() in allowed_laws
            ][:limit]

        expanded_query = self._expand_query(query)
        query_vector = self.vectorizer.transform([expanded_query])
        similarities = cosine_similarity(query_vector, self.document_matrix).ravel()

        ranked_results = []
        normalized_query = self._normalize_text(query)
        query_terms = set(self._analyze(query))
        exact_sections = self._section_candidates(query)

        for index, document in enumerate(self.documents):
            if document.law.lower() not in allowed_laws:
                continue

            score = float(similarities[index])
            score += self._contextual_boost(
                document=document,
                normalized_query=normalized_query,
                query_terms=query_terms,
                exact_sections=exact_sections,
            )

            if score >= min_score:
                ranked_results.append((score, document))

        if not ranked_results and min_score > 0:
            return self.search(query=query, law=law, limit=limit, min_score=0.0)

        top_score = max((score for score, _ in ranked_results), default=0.0)
        ranked_results.sort(
            key=lambda item: (
                item[0],
                item[1].title.lower().startswith(normalized_query),
                item[1].law == "IPC",
            ),
            reverse=True,
        )

        return [
            self._to_result(document, self._normalize_score(score, top_score))
            for score, document in ranked_results[:limit]
        ]

    def _build_documents(self, ipc_sections: Dict, bns_sections: Dict) -> List[LegalDocument]:
        documents = []
        for law, sections in (("IPC", ipc_sections), ("BNS", bns_sections)):
            for section_number, section_data in sections.items():
                section = str(section_data.get("section") or section_number)
                title = str(section_data.get("title") or f"Section {section}")
                description = str(section_data.get("description") or "")

                search_text = " ".join(
                    [
                        law,
                        section,
                        f"section {section}",
                        title,
                        title,
                        title,
                        description,
                    ]
                )
                documents.append(
                    LegalDocument(
                        law=law,
                        section=section,
                        title=title,
                        description=description,
                        search_text=search_text,
                        title_text=self._normalize_text(title),
                    )
                )
        return documents

    def _allowed_laws(self, law: str) -> set:
        if law == "all":
            return {"ipc", "bns"}
        return {law}

    def _expand_query(self, query: str) -> str:
        tokens = self._tokenize(query)
        expansions = []
        for token in tokens:
            expansions.extend(QUERY_EXPANSIONS.get(token, []))
            expansions.extend(QUERY_EXPANSIONS.get(self._stem(token), []))

        if not expansions:
            return query

        return " ".join([query, " ".join(expansions)])

    def _contextual_boost(
        self,
        document: LegalDocument,
        normalized_query: str,
        query_terms: set,
        exact_sections: set,
    ) -> float:
        boost = 0.0

        if document.section.lower() in exact_sections:
            boost += 0.55

        title_terms = set(self._analyze(document.title))
        if query_terms and title_terms:
            title_overlap = len(query_terms.intersection(title_terms)) / math.sqrt(len(query_terms))
            boost += min(title_overlap * 0.16, 0.35)

            high_intent_overlap = query_terms.intersection(HIGH_INTENT_TERMS).intersection(title_terms)
            boost += min(len(high_intent_overlap) * 0.2, 0.45)

        if normalized_query and normalized_query in document.title_text:
            boost += 0.22

        meaningful_phrases = list(self._query_phrases(normalized_query))
        if meaningful_phrases:
            normalized_document = self._normalize_text(
                f"{document.title} {document.description[:1200]}"
            )
            phrase_hits = sum(1 for phrase in meaningful_phrases if phrase in normalized_document)
            boost += min(phrase_hits * 0.08, 0.24)

        if self._looks_like_complaint(query_terms) and document.title_text in LOW_COMPLAINT_VALUE_TITLES:
            boost -= 0.35

        return boost

    def _looks_like_complaint(self, query_terms: set) -> bool:
        complaint_terms = {
            "abus",
            "assault",
            "burn",
            "cheat",
            "death",
            "dowry",
            "fraud",
            "hurt",
            "kill",
            "murder",
            "rape",
            "robbery",
            "sexual",
            "steal",
            "theft",
            "threaten",
        }
        return bool(query_terms.intersection(complaint_terms))

    def _query_phrases(self, normalized_query: str) -> Iterable[str]:
        tokens = [token for token in self._tokenize(normalized_query) if token not in STOPWORDS]
        for size in (3, 2):
            for index in range(0, max(len(tokens) - size + 1, 0)):
                yield " ".join(tokens[index : index + size])

    def _section_candidates(self, query: str) -> set:
        return {match.group(1).lower() for match in SECTION_PATTERN.finditer(query)}

    def _analyze(self, text: str) -> List[str]:
        stems = [
            self._stem(token)
            for token in self._tokenize(text)
            if token not in STOPWORDS and len(token) > 1
        ]
        bigrams = [
            f"{stems[index]} {stems[index + 1]}"
            for index in range(0, max(len(stems) - 1, 0))
        ]
        return stems + bigrams

    def _tokenize(self, text: str) -> List[str]:
        return TOKEN_PATTERN.findall(self._normalize_text(text))

    def _normalize_text(self, text: str) -> str:
        text = (text or "").lower()
        text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _stem(self, token: str) -> str:
        if token.isdigit() or len(token) <= 3:
            return token

        suffix_rules = (
            ("ational", "ate"),
            ("fulness", "ful"),
            ("ousness", "ous"),
            ("iveness", "ive"),
            ("tional", "tion"),
            ("ingly", ""),
            ("edly", ""),
            ("ment", ""),
            ("ness", ""),
            ("ing", ""),
            ("ies", "y"),
            ("ied", "y"),
            ("ly", ""),
            ("ed", ""),
            ("es", ""),
            ("s", ""),
        )
        for suffix, replacement in suffix_rules:
            if suffix == "s" and token.endswith(("ss", "ous")):
                continue
            if token.endswith(suffix) and len(token) - len(suffix) >= 3:
                return token[: -len(suffix)] + replacement
        return token

    def _normalize_score(self, score: float, top_score: float) -> float:
        if top_score <= 0:
            return 0.0
        scaled = score / top_score
        return round(min(max(scaled, 0.0), 1.0), 4)

    def _to_result(self, document: LegalDocument, score: float) -> Dict:
        return {
            "law": document.law,
            "section": document.section,
            "title": document.title,
            "description": document.description,
            "score": score,
        }
