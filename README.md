# TIC Research API

## Overview
The TIC Research API is a modern, AI-powered backend for conducting research on Testing, Inspection, and Certification (TIC) requirements for global trade. It leverages LLMs (like OpenAI), web search, and a robust database to help users discover certifications, standards, and compliance steps for exporting products worldwide.

## Features
- **Chatbot-style API**: Users interact via a single endpoint for seamless Q&A.
- **LLM Integration**: Uses OpenAI for query understanding, workflow routing, and summarization.
- **Web & Domain Search**: Integrates with Perplexity and RAG APIs for up-to-date, authoritative answers.
- **Session & Message Storage**: All user and assistant messages are stored for context and audit.
- **Research Request Tracking**: Every research workflow is logged, including queries, results, and processing time.
- **Analytics**: Tracks usage and performance for continuous improvement.

## Main API Workflow
1. **User sends a message** via `/chat/send` (with `session_id` and `content`).
2. **Message is stored** in the database.
3. **Recent chat history** is retrieved for context.
4. **Domain metadata** is fetched from an external RAG API.
5. **Router (LLM) decides** the best workflow (direct answer or research).
6. **If research is needed**: queries are generated, mapped to websites, and executed in parallel.
7. **Results are summarized** by the LLM and stored as an assistant message.
8. **All actions are logged** for traceability and analytics.

## Key Endpoints
- `POST /chat/send` — Main chat endpoint (stores user message, triggers research, returns answer)
- `POST /research` — (Advanced) Triggers research workflow for a session
- `GET /health` — Health check

## Tech Stack
- **FastAPI** (Python) — API framework
- **PostgreSQL** — Database (async SQLAlchemy)
- **OpenAI** — LLM for routing, query generation, summarization
- **Perplexity AI** — Web/domain search
- **External RAG API** — Domain metadata extraction

## Setup & Running
1. **Clone the repo**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set environment variables** (see `env_example.txt`)
4. **Run the API server**:
   ```bash
   python start_api.py
   ```
5. **Access docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Contributing
- Please open issues or pull requests for improvements or bug fixes.
- See code comments and docstrings for guidance.

## License
MIT (or your preferred license) 