# Polished - Resume Ranking System

A scalable resume sorting and ranking platform with tiered features for recruiters and agencies.

## Features

### Core Service (Free Tier)
- Batch upload of resumes (PDF, DOCX, TXT) - up to 100 per batch
- Automatic text extraction and parsing
- Rule-based scoring across 6 categories
- Automatic ranking by overall score
- CSV/JSON export

### Premium Add-ons
1. **JD Matching** ($29/mo) - Match resumes against job descriptions with skill gap analysis
2. **Deep Analysis** ($99/mo) - AI-powered strengths/weaknesses assessment
3. **Resume Consulting** ($499/mo) - Interactive AI chat for resume improvement

### Revenue System
- Placement tracking with $250 per verified placement
- Verification workflow (pending → verified → paid)

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI
- **Frontend**: React 18 / TypeScript / Vite / Tailwind CSS
- **Storage**: AWS DynamoDB + S3
- **Cache**: Redis
- **Deployment**: Railway (backend) + Vercel (frontend)

## Getting Started

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your AWS credentials
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker (Full Stack)
```bash
docker-compose up -d
```

## API Endpoints

### Batches (Core)
- `POST /api/v1/batches` - Create batch
- `GET /api/v1/batches` - List batches
- `POST /api/v1/batches/{id}/upload` - Upload resume
- `POST /api/v1/batches/{id}/process` - Start processing
- `GET /api/v1/batches/{id}/rankings` - Get rankings
- `POST /api/v1/batches/{id}/export` - Export results

### Placements (Revenue)
- `POST /api/v1/placements` - Report placement
- `GET /api/v1/placements` - List placements
- `POST /api/v1/placements/{id}/verify` - Verify placement

### Consulting (Premium)
- `POST /api/v1/consulting/sessions` - Create session
- `POST /api/v1/consulting/chat` - Send message

## Environment Variables

### Backend (.env)
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=polished-batches-us-east-1
DYNAMODB_TABLE_PREFIX=polished
REDIS_URL=redis://localhost:6379/0
PREMIUM_BYPASS=true
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
```

## Deployment

- **Backend**: Deployed on Railway
- **Frontend**: Deployed on Vercel

## License

MIT
