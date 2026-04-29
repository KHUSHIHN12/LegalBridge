// ─────────────────────────────────────────────
// DATA LOADING
// ─────────────────────────────────────────────
let LEGAL_DATA = null;
let browseFilter = 'all';
let chatHistory = [];

// Data embedded directly - no fetch needed
function loadData() {
  LEGAL_DATA = window.LEGAL_DATA_EMBEDDED;
  console.log('Legal data loaded:', Object.keys(LEGAL_DATA.ipc_sections).length, 'IPC,', Object.keys(LEGAL_DATA.bns_sections).length, 'BNS');
}

loadData();

// ─────────────────────────────────────────────
// TAB SWITCHING
// ─────────────────────────────────────────────
function switchTab(tab) {
  document.querySelectorAll('.tab').forEach((t,i) => {
    const tabs = ['lookup','search','compare'];
    t.classList.toggle('active', tabs[i] === tab);
  });
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
}

// ─────────────────────────────────────────────
// SECTION CARD HTML BUILDER
// ─────────────────────────────────────────────
function buildSectionCard(type, num, title, desc, mappings, mappingType) {
  const isNew = type === 'bns' && (!mappings || mappings.length === 0);
  const cardClass = isNew ? 'new' : type;
  const label = type === 'ipc' ? 'IPC' : 'BNS';
  const mapLabel = type === 'ipc' ? 'BNS' : 'IPC';
  const mapType = type === 'ipc' ? 'bns' : 'ipc';
  
  let mapTagsHTML = '';
  if (isNew) {
    mapTagsHTML = '<span class="map-tag new-section">NEW in BNS</span>';
  } else if (mappings && mappings.length > 0) {
    mapTagsHTML = `<span class="mapping-caption">${mapLabel} equivalent:</span> `;
    mapTagsHTML += mappings.slice(0, 6).map(m => 
      `<span class="map-tag ${mapType}" onclick="showSection('${mapType}','${m}')" title="View ${mapLabel} §${m}">${mapLabel} §${m}</span>`
    ).join('');
    if (mappings.length > 6) mapTagsHTML += `<span class="mapping-more"> +${mappings.length - 6} more</span>`;
  } else {
    mapTagsHTML = `<span class="mapping-empty">No direct ${mapLabel} equivalent found</span>`;
  }

  const shortDesc = desc ? desc.substring(0, 300) + (desc.length > 300 ? '...' : '') : 'Description not available.';

  return `
    <div class="result-card ${cardClass}">
      <div class="result-card-header">
        <span class="section-number">${label} §${num}</span>
        <span class="result-card-title">${title || 'Section ' + num}</span>
      </div>
      <div class="result-card-body">${shortDesc}</div>
      <div class="result-card-footer">${mapTagsHTML}</div>
    </div>`;
}

// ─────────────────────────────────────────────
// SHOW SECTION (navigate to)
// ─────────────────────────────────────────────
function showSection(type, num) {
  switchTab('lookup');
  if (type === 'ipc') {
    document.getElementById('ipcLookupInput').value = num;
    performLookup('ipc');
  } else {
    document.getElementById('bnsLookupInput').value = num;
    performLookup('bns');
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ─────────────────────────────────────────────
// QUICK LOOKUP (sidebar)
// ─────────────────────────────────────────────
function lookupIPC() {
  const num = document.getElementById('ipcInput').value.trim().toUpperCase();
  if (!num || !LEGAL_DATA) return;
  
  const sec = LEGAL_DATA.ipc_sections[num] || LEGAL_DATA.ipc_sections[num.toLowerCase()];
  const bnsMappings = LEGAL_DATA.ipc_to_bns[num] || LEGAL_DATA.ipc_to_bns[num.toLowerCase()] || [];
  
  const container = document.getElementById('lookupResult');
  
  if (!sec) {
    container.innerHTML = `<div class="status-alert">IPC Section ${num} not found in database.</div>`;
    return;
  }
  
  container.innerHTML = buildSectionCard('ipc', num, sec.title, sec.description, bnsMappings, 'bns');
}

function lookupBNS() {
  const num = document.getElementById('bnsInput').value.trim();
  if (!num || !LEGAL_DATA) return;
  
  const sec = LEGAL_DATA.bns_sections[num];
  const ipcMappings = LEGAL_DATA.bns_to_ipc[num] || [];
  
  const container = document.getElementById('lookupResult');
  
  if (!sec) {
    container.innerHTML = `<div class="status-alert">BNS Section ${num} not found in database.</div>`;
    return;
  }
  
  container.innerHTML = buildSectionCard('bns', num, sec.title, sec.description, ipcMappings, 'ipc');
}

// ─────────────────────────────────────────────
// DEDICATED LOOKUP TAB
// ─────────────────────────────────────────────
function performLookup(type) {
  if (!LEGAL_DATA) return;
  
  if (type === 'ipc') {
    const num = document.getElementById('ipcLookupInput').value.trim().toUpperCase();
    const container = document.getElementById('ipcLookupResult');
    if (!num) return;
    
    const sec = LEGAL_DATA.ipc_sections[num] || LEGAL_DATA.ipc_sections[num.toLowerCase()];
    const bnsMappings = LEGAL_DATA.ipc_to_bns[num] || LEGAL_DATA.ipc_to_bns[num.toLowerCase()] || [];
    
    if (!sec) {
      container.innerHTML = `<div class="status-alert status-alert-spacious">? IPC Section ${num} not found.</div>`;
      return;
    }
    
    let html = buildSectionCard('ipc', num, sec.title, sec.description, bnsMappings, 'bns');
    
    // Show all BNS mappings with full details
    if (bnsMappings.length > 0) {
      html += `<div class="section-subheading">BNS Equivalent Sections</div>`;
      bnsMappings.forEach(bnsNum => {
        const bnsSec = LEGAL_DATA.bns_sections[bnsNum];
        if (bnsSec) {
          html += buildSectionCard('bns', bnsNum, bnsSec.title, bnsSec.description, LEGAL_DATA.bns_to_ipc[bnsNum] || [], 'ipc');
        }
      });
    }
    
    container.innerHTML = html;
    
  } else {
    const num = document.getElementById('bnsLookupInput').value.trim();
    const container = document.getElementById('bnsLookupResult');
    if (!num) return;
    
    const sec = LEGAL_DATA.bns_sections[num];
    const ipcMappings = LEGAL_DATA.bns_to_ipc[num] || [];
    
    if (!sec) {
      container.innerHTML = `<div class="status-alert status-alert-spacious">? BNS Section ${num} not found.</div>`;
      return;
    }
    
    let html = buildSectionCard('bns', num, sec.title, sec.description, ipcMappings, 'ipc');
    
    if (ipcMappings.length > 0) {
      html += `<div class="section-subheading">IPC Source Sections</div>`;
      ipcMappings.forEach(ipcNum => {
        const ipcSec = LEGAL_DATA.ipc_sections[ipcNum];
        if (ipcSec) {
          html += buildSectionCard('ipc', ipcNum, ipcSec.title, ipcSec.description, LEGAL_DATA.ipc_to_bns[ipcNum] || [], 'bns');
        }
      });
    } else if (!sec) {
      // nothing
    } else {
      html += `<div class="new-section-note">? This is a <strong>new section</strong> added in BNS 2023 with no direct IPC equivalent.</div>`;
    }
    
    container.innerHTML = html;
  }
}

// ─────────────────────────────────────────────
// BROWSE / SEARCH
// ─────────────────────────────────────────────
let browseTimeout = null;
function browseSearch() {
  clearTimeout(browseTimeout);
  browseTimeout = setTimeout(_doBrowseSearch, 200);
}

// New/deleted BNS sections
const NEW_BNS_SECTIONS = new Set(['48','69','95','111','112','113','152','226','304']);
const DELETED_IPC_SECTIONS = new Set(['124A','309','310','311','377','497','153AA']);

function _doBrowseSearch() {
  if (!LEGAL_DATA) return;
  const query = document.getElementById('browseInput').value.trim().toLowerCase();
  const container = document.getElementById('browseResults');
  
  if (!query && browseFilter === 'all') {
    container.innerHTML = `<div class="no-results"><div class="icon">📚</div><p>Type a keyword to search through IPC and BNS sections</p></div>`;
    return;
  }
  
  let results = [];
  
  if (browseFilter !== 'bns' && browseFilter !== 'new') {
    // Search IPC
    Object.entries(LEGAL_DATA.ipc_sections).forEach(([num, sec]) => {
      if (browseFilter === 'deleted' && !DELETED_IPC_SECTIONS.has(num)) return;
      if (browseFilter === 'all' || browseFilter === 'ipc' || browseFilter === 'deleted') {
        const matches = !query || 
          num.toLowerCase().includes(query) ||
          (sec.title || '').toLowerCase().includes(query) ||
          (sec.description || '').toLowerCase().includes(query);
        if (matches) {
          results.push({ type: 'ipc', num, ...sec });
        }
      }
    });
  }
  
  if (browseFilter !== 'ipc' && browseFilter !== 'deleted') {
    // Search BNS
    Object.entries(LEGAL_DATA.bns_sections).forEach(([num, sec]) => {
      const isNew = NEW_BNS_SECTIONS.has(num) || !(LEGAL_DATA.bns_to_ipc[num] || []).length;
      if (browseFilter === 'new' && !isNew) return;
      const matches = !query || 
        num.toLowerCase().includes(query) ||
        (sec.title || '').toLowerCase().includes(query) ||
        (sec.description || '').toLowerCase().includes(query);
      if (matches) {
        results.push({ type: 'bns', num, ...sec });
      }
    });
  }
  
  // Limit results
  const total = results.length;
  results = results.slice(0, 30);
  
  if (results.length === 0) {
    container.innerHTML = `<div class="no-results"><div class="icon">🔍</div><p>No sections found matching "${query}"</p></div>`;
    return;
  }
  
  let html = `<div class="results-meta">Showing ${results.length} of ${total} results</div>`;
  html += '<div class="results-grid">';
  results.forEach(r => {
    const mappings = r.type === 'ipc' 
      ? (LEGAL_DATA.ipc_to_bns[r.num] || [])
      : (LEGAL_DATA.bns_to_ipc[r.num] || []);
    html += buildSectionCard(r.type, r.num, r.title, r.description, mappings, r.type === 'ipc' ? 'bns' : 'ipc');
  });
  html += '</div>';
  
  container.innerHTML = html;
}

function setFilter(filter, btn) {
  browseFilter = filter;
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  browseSearch();
}



// ─────────────────────────────────────────────
// AI CHAT
// ─────────────────────────────────────────────
function setPrompt(text) {
  document.getElementById('chatInput').value = text;
  autoResize(document.getElementById('chatInput'));
  document.getElementById('chatInput').focus();
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function appendMessage(role, html) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = `message ${role}`;
  const avatar = role === 'ai' ? '⚖' : '👤';
  div.innerHTML = `
    <div class="msg-avatar ${role}">${avatar}</div>
    <div class="msg-bubble"><div class="msg-content">${html}</div></div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function showTyping() {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'message ai';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="msg-avatar ai">⚖</div>
    <div class="msg-bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

function buildSystemPrompt() {
  if (!LEGAL_DATA) return '';
  
  // Build a concise section index for the AI
  const ipcKeys = Object.keys(LEGAL_DATA.ipc_sections).slice(0, 200);
  const bnsKeys = Object.keys(LEGAL_DATA.bns_sections).slice(0, 200);
  
  // Key sections to always include
  const keySections = ['99','100','101','102','103','104','105','106','107','108','109',
    '114','115','116','117','118','119','120','121','122','123','124','125','126','127',
    '128','129','130','131','132','133','137','138','143','147','151','152',
    '300','301','302','303','304','304A','304B','305','306','307','308','319','320',
    '321','322','323','324','325','326','327','328','329','330','331','332','333',
    '354','354A','354B','354C','354D','363','366','370','372','373','374','375','376',
    '376A','376B','376D','377','378','379','380','382','383','384','385','386','387',
    '388','389','390','391','392','395','396','397','398','399','400','401','402',
    '403','404','405','406','407','408','409','410','411','412','413','414',
    '415','416','417','418','419','420','421','422','423','424','425','426','427',
    '441','442','443','445','447','448','449','450','451','452','453','454','455',
    '456','457','458','459','460','461','462','463','464','465','466','467','468',
    '469','470','471','472','473','474','475','476','477','477A','489A','489B','489C',
    '489D','489E','491','493','494','495','496','497','498','498A','499','500','501',
    '502','503','504','505','506','507','508','509','510','511',
    '120A','120B','121A','153A','153B','228A','295A','304B','354A','354B','354C','354D',
    '363A','364A','366A','366B','370A','376A','376AB','376B','376C','376D','376DA','376DB',
    '376E','477A','489A','489B','489C','489D','498A'];
  
  let ipcIndex = '';
  keySections.forEach(num => {
    const sec = LEGAL_DATA.ipc_sections[num];
    if (sec) {
      const bns = (LEGAL_DATA.ipc_to_bns[num] || []).join(', ') || 'deleted/no equivalent';
      ipcIndex += `IPC ${num}: ${sec.title} → BNS: ${bns}\n`;
    }
  });
  
  // BNS new sections
  let bnsNew = '';
  ['48','69','95','111','112','113','152','226','304'].forEach(num => {
    const sec = LEGAL_DATA.bns_sections[num];
    if (sec) bnsNew += `BNS ${num}: ${sec.title} (NEW - no IPC equivalent)\n`;
  });
  
  return `You are LegalBridge, an expert AI legal assistant specializing in Indian criminal law, specifically the Indian Penal Code (IPC) 1860 and the new Bharatiya Nyaya Sanhita (BNS) 2023 which replaced IPC.

Your capabilities:
1. Analyze incident/complaint descriptions and identify applicable IPC and BNS sections
2. Map IPC sections to their BNS equivalents and vice versa
3. Explain legal sections in plain, accessible language
4. Highlight key differences between IPC and BNS provisions

IMPORTANT IPC→BNS KEY MAPPINGS (always reference actual section numbers):
${ipcIndex}

NEW SECTIONS in BNS 2023 (no IPC equivalent):
${bnsNew}

DELETED in BNS 2023:
- IPC 124A (Sedition) - DELETED
- IPC 377 (Unnatural offences) - DELETED  
- IPC 497 (Adultery) - DELETED
- IPC 309 (Attempt to suicide) - DELETED

FORMATTING RULES:
- Always cite specific section numbers: "IPC §302" or "BNS §103"
- When analyzing incidents, list the most relevant sections first
- Format section references as: **IPC §[number]** or **BNS §[number]**
- Be concise but thorough
- Add a disclaimer that this is for educational reference only, not legal advice
- When mapping sections, show both the source and target section numbers and titles`;
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;
  
  const sendBtn = document.getElementById('sendBtn');
  sendBtn.disabled = true;
  input.value = '';
  input.style.height = 'auto';
  
  // Add user message
  appendMessage('user', escapeHtml(text));
  
  // Add to history
  chatHistory.push({ role: 'user', content: text });
  
  // Show typing
  showTyping();
  
  try {
    const systemPrompt = buildSystemPrompt();
    
    const messages = chatHistory.slice(-8); // Keep last 8 messages for context
    
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1000,
        system: systemPrompt,
        messages: messages
      })
    });
    
    const data = await response.json();
    
    hideTyping();
    
    if (data.content && data.content[0]) {
      const aiText = data.content[0].text;
      chatHistory.push({ role: 'assistant', content: aiText });
      
      // Format the response
      const formatted = formatAIResponse(aiText);
      appendMessage('ai', formatted);
    } else if (data.error) {
      appendMessage('ai', `<p class="text-danger">Error: ${data.error.message || 'Failed to get response'}</p>`);
    }
  } catch (err) {
    hideTyping();
    appendMessage('ai', `<p class="text-danger">Connection error. Please check your network and try again.</p>`);
    console.error(err);
  }
  
  sendBtn.disabled = false;
  input.focus();
}

function formatAIResponse(text) {
  // Convert markdown-like formatting to HTML
  let html = escapeHtml(text);
  
  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // IPC/BNS section tags - highlight section references
  html = html.replace(/IPC\s+§(\w+)/g, '<span class="section-tag ipc">IPC §$1</span>');
  html = html.replace(/BNS\s+§(\w+)/g, '<span class="section-tag bns">BNS §$1</span>');
  html = html.replace(/IPC\s+[Ss]ection\s+(\w+)/g, '<span class="section-tag ipc">IPC §$1</span>');
  html = html.replace(/BNS\s+[Ss]ection\s+(\w+)/g, '<span class="section-tag bns">BNS §$1</span>');
  
  // Line breaks to paragraphs
  const lines = html.split('\n');
  let result = '';
  let inList = false;
  
  for (let line of lines) {
    line = line.trim();
    if (!line) {
      if (inList) { result += '</ul>'; inList = false; }
      continue;
    }
    if (line.startsWith('- ') || line.startsWith('• ')) {
      if (!inList) { result += '<ul>'; inList = true; }
      result += `<li>${line.substring(2)}</li>`;
    } else if (line.match(/^\d+\.\s/)) {
      if (!inList) { result += '<ul>'; inList = true; }
      result += `<li>${line.replace(/^\d+\.\s/, '')}</li>`;
    } else {
      if (inList) { result += '</ul>'; inList = false; }
      result += `<p>${line}</p>`;
    }
  }
  if (inList) result += '</ul>';
  
  return result || `<p>${html}</p>`;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Clear chat
function clearChat() {
  chatHistory = [];
  const container = document.getElementById('chatMessages');
  container.innerHTML = '<div class="cleared-msg">Chat cleared. Start a new conversation.</div>';
}
