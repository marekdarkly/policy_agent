# ToggleHealth Multi-Agent Assistant UI

A modern, standalone web interface for the ToggleHealth multi-agent system.

## 🎯 Architecture

```
Frontend (React + Vite)  →  Backend (FastAPI)  →  Multi-Agent Workflow
  Port 3000                   Port 8000              (LangGraph)
```

## 🚀 Quick Start

### 1. Start the Backend

```bash
cd ui/backend
pip install -r requirements.txt
python server.py
```

Backend runs on: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### 2. Start the Frontend

```bash
cd ui/frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:3000`

### 3. Open in Browser

Navigate to `http://localhost:3000`

## 📁 Project Structure

```
ui/
├── backend/
│   ├── server.py           # FastAPI server
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   ├── App.css        # Styling
│   │   ├── main.tsx       # React entry point
│   │   └── index.css      # Global styles
│   ├── index.html         # HTML template
│   ├── vite.config.ts     # Vite configuration
│   ├── tsconfig.json      # TypeScript config
│   └── package.json       # Node dependencies
└── public/
    └── assets/
        └── ToggleAvatar.png  # Chat avatar
```

## ✨ Features

### Real-Time Agent Status
The UI displays a dynamic status box showing which agent is currently working:

- 🔍 **Triage Router**: Analyzing your question
- 📋 **Policy Specialist**: Retrieving policy information
- 🏥 **Provider Specialist**: Finding healthcare providers
- 📅 **Scheduler Specialist**: Checking availability
- ✨ **Brand Voice**: Crafting the response

The status box disappears when the response is ready!

### Metrics Panel
After each response, users can expand the metrics panel to see:

- **Query Type**: The classified intent (e.g., POLICY_QUESTION, PROVIDER_LOOKUP)
- **Confidence**: Model's confidence in routing decision
- **Agent Flow**: Visual representation of which agents were invoked
- **RAG Documents**: Number of documents retrieved by each specialist
- **Agent Count**: Total agents involved in the response

### User Experience
- Gradient header with ToggleHealth branding
- Smooth animations for agent transitions
- Feedback buttons (good/bad service)
- Responsive design (mobile-friendly)
- Auto-scroll to latest message

## 🔧 Development

### Backend Development

```bash
cd ui/backend
python server.py
```

The backend auto-reloads on file changes.

### Frontend Development

```bash
cd ui/frontend
npm run dev
```

Vite provides hot module replacement (HMR) for instant updates.

### Building for Production

```bash
cd ui/frontend
npm run build
npm run preview
```

## 🎨 Customization

### Styling
Modify `ui/frontend/src/App.css` to customize colors, fonts, and layout.

### Avatar
Replace `ui/public/assets/ToggleAvatar.png` with your own avatar image.

### Agent Icons
Edit the `icon` field in `ui/backend/server.py` to customize agent emojis.

## 🧪 Testing

### Test the Backend API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"userInput": "What is my copay for specialist visits?"}'
```

### Test the Health Check

```bash
curl http://localhost:8000/health
```

## 📝 API Reference

### POST `/api/chat`

**Request:**
```json
{
  "userInput": "What are my dental benefits?",
  "userName": "Marek Poliks",
  "location": "San Francisco, CA",
  "policyId": "TH-HMO-GOLD-2024",
  "coverageType": "Gold HMO"
}
```

**Response:**
```json
{
  "response": "Your Gold HMO plan includes comprehensive dental coverage...",
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "agentFlow": [
    {
      "agent": "triage_router",
      "name": "Triage Router",
      "status": "complete",
      "confidence": 0.95,
      "icon": "🔍"
    },
    {
      "agent": "policy_specialist",
      "name": "Policy Specialist",
      "status": "complete",
      "rag_docs": 3,
      "icon": "📋"
    },
    {
      "agent": "brand_voice",
      "name": "Brand Voice",
      "status": "complete",
      "icon": "✨"
    }
  ],
  "metrics": {
    "query_type": "POLICY_QUESTION",
    "confidence": 0.95,
    "agent_count": 3,
    "rag_enabled": true
  }
}
```

## 🐛 Troubleshooting

**Backend not connecting to LaunchDarkly?**
- Check your `.env` file in the project root
- Verify `LAUNCHDARKLY_SDK_KEY` is set correctly
- Ensure `LAUNCHDARKLY_ENABLED=true`

**AWS credentials expired?**
- Run `make aws-login` from the project root
- Or manually: `aws sso login --profile marek`

**Frontend can't reach backend?**
- Ensure backend is running on port 8000
- Check CORS settings in `server.py`
- Verify proxy configuration in `vite.config.ts`

**Avatar not displaying?**
- Ensure `ui/public/assets/ToggleAvatar.png` exists
- Check browser console for 404 errors
- Use relative path `/assets/ToggleAvatar.png`

## 📦 Dependencies

### Backend
- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Data validation

### Frontend
- React 18: UI framework
- Vite: Build tool
- TypeScript: Type safety
- react-spinners: Loading animations

## 🔗 Related Documentation

- [Main README](../README.md)
- [LaunchDarkly Integration](../LAUNCHDARKLY.md)
- [Evaluation System](../EVALUATION_PROMPTS.md)
- [Quick Start Guide](../QUICKSTART.md)

---

Built with ❤️ for ToggleHealth

