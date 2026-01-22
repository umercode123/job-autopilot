# Job Autopilot 🚀

[![GitHub stars](https://img.shields.io/github/stars/Schlaflied/job-autopilot?style=social)](https://github.com/Schlaflied/job-autopilot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Schlaflied/job-autopilot?style=social)](https://github.com/Schlaflied/job-autopilot/network/members)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**AI-powered job application automation system** that streamlines your job search workflow using GPT-4o, automated scraping, resume optimization, LinkedIn outreach, and intelligent cold email campaigns.

> **Perfect for**: Job seekers in EdTech, L&D, AI Product Management, and Automation fields

---

## ✨ Features

### 🎯 Intelligent Job Discovery
- 🔍 **Automated Indeed Scraping** via Apify
- 🤖 **AI-Powered Job Scoring** (0-10 rating based on your profile)
- 📊 **Smart Categorization** (EdTech, AI PM, Automation, L&D)
- 💾 **Database Caching** (Neon PostgreSQL + Local SQLite fallback)
- 📦 **Load Cached Jobs** (reuse previous searches, save API quota)

### 📄 Resume Export & Optimization
- 📤 **Multi-Format Upload**: Support PDF, DOCX, and Markdown master resumes
- 🎨 **Professional Templates**: 4 ATS-friendly templates (single/two-column, classic/modern)
- 🧠 **GPT-4o Powered**: Resume optimization uses GPT-4o for higher accuracy
- 📊 **ATS Scoring**: Real-time ATS compatibility score with keyword matching
- 🎯 **Job-Tailored Resumes**: AI optimizes resume for each job description
- 🔒 **Anti-Hallucination**: Iron-clad data protection - dates, locations locked

### ☕ Coffee Chat Center ✨ NEW
- 🎓 **School Configuration**: Set your alumni schools (priority-ranked)
- 🏷️ **Target Fields**: Define your professional interests (L&D, AI, etc.)
- 📋 **Job Integration**: Link high-value jobs to LinkedIn search
- 🔗 **One-Click LinkedIn Launch**: Search alumni directly from UI

### 🔗 LinkedIn Automation ✨ NEW
- 🌐 **Chrome DevTools MCP**: AI-friendly browser automation via accessibility tree
- 🎓 **Alumni Search**: Find 2nd-degree connections from your schools
- 🤖 **AI Agents**:
  - **ContactRankerAgent**: Priority scoring (0-100) based on job match, alumni status
  - **ScamDetectionAgent**: Filter suspicious profiles automatically
  - **PersonalizationAgent**: GPT-4 powered message generation
- 🧠 **Memory Layer**: ChromaDB vector storage for learning from successful messages
- 📨 **Auto-Connect**: Send connection requests with rate limiting (10-20s delays)
- 💾 **Persistent Profile**: Uses dedicated Chrome profile (no conflict with personal Chrome)

### 📧 Email Center
- 📝 **Draft Cold Emails**: AI-generated personalized emails
- 📬 **Gmail Integration**: Create drafts directly in Gmail
- 📊 **Email Statistics**: Track drafts, sent, replied counts
- ⏰ **Follow-up Queue**: Auto-generate follow-up drafts

### 📊 Dashboard
- 📈 **Kanban Board**: Visual pipeline (To Apply → Sent → Replied → Interview)
- 📚 **Applied History**: Manage manually marked applications
- 🎯 **One-Click Apply**: Move jobs through stages
- 📧 **Status Tracking**: Real-time application status

---

## 🏗️ Architecture

### Project Overview
![Project Architecture](Job%20Autopilot%20-%20Complete%20Project%20Architecture.png)

### Coffee Chat Data Flow
![Data Flow](Coffee%20chat%20center%20Data%20Flow%20Diagram.png)

### LinkedIn Automation Flow
![LinkedIn Flow](LinkedIn%20Automation%20Flow.png)

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **AI/LLM** | OpenAI GPT-4o / GPT-4o-mini |
| **Frontend** | Streamlit 1.30+ |
| **Backend** | Python 3.11+ |
| **Database** | Neon PostgreSQL (cloud) |
| **Job Scraping** | Apify (Indeed Actor) |
| **LinkedIn Automation** | Chrome DevTools MCP (Puppeteer-based) |
| **Memory Layer** | ChromaDB (Vector Database) |
| **Email** | Gmail API (OAuth 2.0) |
| **Resume** | python-docx, ReportLab (PDF) |
| **ORM** | SQLAlchemy 2.0 |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for Chrome DevTools MCP)
- **Git**

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Schlaflied/job-autopilot.git
cd job-autopilot

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Initialize database
python scripts/init_database.py
python scripts/init_coffee_chat_db.py

# 6. Run the application
streamlit run streamlit_app.py --server.port=8502
```

**Access the app**: http://localhost:8502

---

## 📁 Project Structure

```
job-autopilot/
├── modules/
│   ├── ai_agent.py              # GPT-4o integration (scoring, resume, emails)
│   ├── coffee_chat_agents.py    # ✨ AI Agents (Ranker, Scam, Personalization)
│   ├── coffee_chat_memory.py    # ✨ ChromaDB Memory Layer
│   ├── coffee_chat_models.py    # SQLAlchemy models for Coffee Chat
│   ├── linkedin_automation.py   # ✨ LinkedIn search and automation
│   ├── job_scraper.py           # Apify job scraper with caching
│   ├── job_contact_integrator.py # Job + Contact integration
│   ├── gmail_service.py         # Gmail API integration
│   ├── database.py              # SQLAlchemy models (Neon PostgreSQL)
│   ├── resume_generator.py      # Resume PDF/DOCX generation
│   └── logger_config.py         # Centralized logging
├── pages/
│   ├── coffee_chat_center.py    # ✨ Coffee Chat Dashboard
│   └── user_profile.py          # ✨ School & Fields Configuration
├── scripts/
│   ├── linkedin_auto_connect.py # ✨ End-to-end LinkedIn automation
│   ├── init_database.py         # Database initialization
│   └── init_coffee_chat_db.py   # Coffee Chat tables
├── docs/
│   └── COFFEE_CHAT_PLAN/        # LinkedIn & Coffee Chat documentation
├── streamlit_app.py             # Main Streamlit UI
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## ⚙️ Configuration

### Required API Keys

#### 1. **OpenAI API** (AI features)
```env
OPENAI_API_KEY=sk-proj-your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```
- Get key: https://platform.openai.com/api-keys

#### 2. **Apify API** (Job scraping)
```env
APIFY_API_TOKEN=apify_api_your_token_here
```
- Get token: https://console.apify.com/account/integrations

#### 3. **Neon PostgreSQL** (Database)
```env
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require
```
- Get database: https://neon.tech/

#### 4. **Gmail API** (Email automation)
```env
GMAIL_CREDENTIALS_PATH=./data/credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=./data/credentials/gmail_token.json
```

---

## 🔗 LinkedIn Automation Guide

### Setup

1. **Configure User Profile**:
   - Go to User Profile page
   - Add your schools (e.g., "University of Western Ontario")
   - Add target fields (e.g., "Learning & Development")

2. **Search Jobs**:
   - Go to Coffee Chat Center
   - Load high-value jobs (score ≥ 7)
   - Select companies to search

3. **Launch LinkedIn**:
   - Click "Search LinkedIn for X Companies"
   - Click "🌐 Launch Chrome & Connect"
   - Chrome opens → Login to LinkedIn (first time only)
   - Script automatically searches and sends connections

### How It Works

```
1. 📋 Select Jobs in Coffee Chat Center
            ↓
2. 🔍 Click "Search LinkedIn" → Extracts company domains
            ↓
3. 🌐 Click "Launch Chrome" → Opens LinkedIn in new Chrome profile
            ↓
4. 🔐 Login to LinkedIn (first time only - session persists)
            ↓
5. 🎓 Searches: "[Company] + [Your School]"
            ↓
6. 🧠 AI Processing:
   - Memory Dedup → Skip already contacted
   - ScamDetection → Filter suspicious profiles
   - ContactRanker → Sort by priority score
            ↓
7. 📨 Auto-Send Connection Requests
   - No notes (saves quota)
   - 10-20s delays (rate limiting)
   - Saves to Memory Layer
            ↓
8. 📊 Summary: X sent, Y failed, Memory stats
```

### Command Line Usage

```bash
# Direct script execution
python scripts/linkedin_auto_connect.py --company "google.com" --school "University of Western Ontario" --limit 5
```

---

## 💰 Cost Estimate

| Service | Cost | Notes |
|---------|------|-------|
| OpenAI GPT-4o-mini | ~$5-10/mo | Job scoring + resume + emails |
| OpenAI Embeddings | ~$0.30/1000 contacts | Memory Layer vectors |
| Apify (Indeed scraper) | $0 (free tier) | $5 free credit |
| Neon PostgreSQL | $0 (free tier) | 0.5GB storage |
| Gmail API | $0 | Free for personal use |
| **Total** | **$5-10/mo** | Scalable to 100+ applications |

---

## 🐛 Troubleshooting

### "Chrome already running"
```powershell
taskkill /F /IM chrome.exe
```

### "LinkedIn not loading"
- The script uses a dedicated profile at `C:/temp/linkedin-automation-profile`
- First run requires manual LinkedIn login
- Login persists for future runs

### "No 2nd degree connections found"
- Try different company/school combinations
- Some companies have few alumni in your network

---

## 📜 License

This project is licensed under **GNU Affero General Public License v3.0 (AGPL-3.0)**.

- ✅ Free to use, modify, distribute
- ⚠️ Must open-source modifications under same license
- ⚠️ Network users entitled to source code

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o API
- **Google Chrome DevTools Team** for Chrome DevTools MCP
- **Apify** for job scraping infrastructure
- **Neon** for free PostgreSQL tier
- **ChromaDB** for vector database
- **[Resume-Matcher](https://github.com/srbhr/Resume-Matcher)** for inspiring our PDF/DOCX parsing approach using `pdfminer.six` and `docx2txt`
- Job seekers worldwide 💪

---

## 🎯 Roadmap

- [x] LinkedIn auto-connect with AI agents
- [x] Memory layer for learning from successful messages
- [ ] Coffee chat message automation (post-connection)
- [ ] Multi-language support
- [ ] Interview prep AI coach

---

<div align="center">

**⭐ Star this repo if it helped you land a job! ⭐**

[Report Bug](https://github.com/Schlaflied/job-autopilot/issues) · [Request Feature](https://github.com/Schlaflied/job-autopilot/issues)

</div>
