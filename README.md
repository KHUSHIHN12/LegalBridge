# legalbridge

# ⚖️ LegalBridge – Stage 1

Map complaints to IPC and BNS legal sections using a simple Flask + HTML app.

## 📁 Project Structure

```
legalbridge/
 ├── frontend/
 │    └── index.html        ← Open this in your browser
 ├── backend/
 │    ├── app.py            ← Flask API
 │    └── requirements.txt  ← Python dependencies
 └── data/
      └── sections.json     ← IPC/BNS legal data
```

## 🚀 How to Run

### Step 1 – Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2 – Start the backend
```bash
python app.py
```
You should see:
```
Starting LegalBridge Backend...
API running at: http://localhost:5000
```

### Step 3 – Open the frontend
Open `frontend/index.html` in your browser (just double-click the file).

---

## 🧪 Test It

Enter this complaint:
```
Someone threatened me and asked for money
```

Expected result:
```
IPC 384 – Extortion
BNS 308 – Extortion
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/search` | Search by complaint text |
| GET | `/api/sections` | List all sections |

### Example API call:
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"complaint": "Someone threatened me and asked for money"}'
```

---

## ✅ Stage 1 Checklist
- [x] User enters complaint
- [x] Backend finds IPC section
- [x] Backend shows BNS mapping
- [ ] Stage 2: Push to GitHub
- [ ] Stage 3: Add CI/CD (GitHub Actions)
- [ ] Stage 4: Add Docker
- [ ] Stage 5: Add Kubernetes
