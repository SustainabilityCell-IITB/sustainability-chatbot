---
title: Sustainability Cell Chatbot
emoji: 🌱
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# IIT Bombay Sustainability Cell Chatbot

AI-powered chatbot for the Sustainability Cell at IIT Bombay. Ask questions about sustainability initiatives, events, team members, and more.

## API Endpoints

- `GET /` - Chat UI
- `POST /api/query` - Send a query
- `POST /api/clear` - Clear conversation history
- `GET /health` - Health check

## Usage

```bash
curl -X POST https://YOUR-SPACE.hf.space/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the Sustainability Cell?"}'
```
