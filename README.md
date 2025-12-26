# Polished

AI-powered resume review agent with 20 years of tech hiring expertise.

![Polished](https://img.shields.io/badge/Powered%20by-Polished%20AI-667eea)
![License](https://img.shields.io/badge/license-MIT-green)

## Overview

Polished is an intelligent resume review tool that provides expert feedback, ATS optimization, and professional rewrites. Built with React and FastAPI, it leverages Claude AI to deliver insights from 20+ years of simulated hiring experience at top tech companies.

## Features

- **Expert Analysis** - AI trained on insights from reviewing 50,000+ resumes
- **ATS Optimization** - Ensure your resume passes Applicant Tracking Systems
- **Interactive Chat** - Get specific advice, rewrites, and improvements through natural conversation
- **Live Preview** - Side-by-side resume preview that updates in real-time
- **PDF Export** - Download your polished resume as a professional PDF
- **Factual Accuracy** - AI never invents details, only enhances what you provide

## Tech Stack

**Frontend**
- React 18 + TypeScript
- Vite
- React Router
- Axios
- Lucide React (icons)
- html2pdf.js

**Backend**
- FastAPI
- Python 3.9+
- Anthropic Claude API
- PyPDF2, python-docx (resume parsing)

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.9+
- Anthropic API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/IParikh1/Polished.git
   cd Polished
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt

   # Create .env file with your API key
   echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start the backend** (port 8001)
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
   ```

2. **Start the frontend** (port 5173)
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open the app**
   - Landing page: http://localhost:5173
   - App: http://localhost:5173/app

## Usage

1. Visit the landing page and click "Polish My Resume"
2. Upload your resume (PDF, DOCX, or TXT)
3. Review the initial expert analysis
4. Chat with the AI to get specific improvements
5. View the live preview as your resume is rewritten
6. Download the polished PDF

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload and analyze a resume |
| `/api/chat` | POST | Continue conversation with the agent |
| `/api/session/{id}` | GET | Get session information |
| `/api/session/{id}` | DELETE | Delete a session |

## Project Structure

```
Polished/
├── backend/
│   ├── app/
│   │   ├── api/routes.py        # API endpoints
│   │   ├── core/config.py       # Configuration
│   │   ├── models/schemas.py    # Pydantic models
│   │   └── services/
│   │       ├── llm_service.py   # Claude API integration
│   │       ├── resume_agent.py  # Expert agent logic
│   │       └── resume_parser.py # PDF/DOCX parsing
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Landing & App pages
│   │   └── main.tsx
│   └── package.json
└── README.md
```

## License

MIT

---

**Powered by Polished AI**
