# Job Autopilot - Streamlit Frontend
# Main UI for job search automation

import streamlit as st
import sys
import os

# Add modules to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.logger_config import streamlit_logger
from modules.job_scraper import JobScraper
from modules.ai_agent import ai_agent
from modules.database import SessionLocal, Job, Application
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Job Autopilot 🚀",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .job-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background: white;
    }
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .score-high {background: #10b981; color: white;}
    .score-medium {background: #f59e0b; color: white;}
    .score-low {background: #ef4444; color: white;}
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = ai_agent.demo_mode

# Sidebar navigation
with st.sidebar:
    st.markdown("### 🚀 Job Autopilot")
    st.markdown("---")
    
    page = st.radio(
        "Navigate",
        ["🔍 Job Search", "📊 Dashboard", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Demo mode indicator
    if st.session_state.demo_mode:
        st.warning("⚠️ **DEMO MODE**\nAPI keys not configured.\nUsing mock data.")
    else:
        st.success("✅ API Connected")
    
    st.markdown("---")
    st.markdown("**Stats**")
    st.metric("Jobs Found", len(st.session_state.jobs))
    st.metric("Applications", 0)

# Main content
if page == "🔍 Job Search":
    st.markdown('<h1 class="main-header">Job Search 🔍</h1>', unsafe_allow_html=True)
    st.markdown("Find and score job opportunities with AI")
    
    # Search form
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        keywords = st.text_input(
            "Keywords",
            value="Instructional Design, AI PM, Automation",
            help="Comma-separated job titles or skills"
        )
    
    with col2:
        location = st.text_input(
            "Location",
            value="Ontario, Canada"
        )
    
    with col3:
        max_jobs = st.number_input(
            "Max Jobs",
            min_value=5,
            max_value=50,
            value=10
        )
    
    col4, col5 = st.columns(2)
    with col4:
        job_type = st.selectbox("Job Type", ["fulltime", "parttime", "contract"])
    with col5:
        remote = st.selectbox("Remote", ["hybrid", "remote", "onsite"])
    
    if st.button("🔍 Search Jobs", type="primary", use_container_width=True):
        with st.spinner("Searching jobs..."):
            try:
                # Demo mode: create sample jobs
                if st.session_state.demo_mode:
                    st.session_state.jobs = [
                        {
                            "id": 1,
                            "title": "Instructional Designer",
                            "company": "EdTech Solutions Inc.",
                            "location": "Toronto, ON (Remote)",
                            "salary": "$60,000 - $75,000",
                            "description": "Looking for an experienced instructional designer to develop engaging online courses...",
                            "is_remote": True,
                            "job_url": "https://example.com/job1",
                            "posted_date": datetime.now(),
                            "match_score": 9,
                            "match_reasoning": "Perfect fit: EdTech role (+4) | Great salary (+3) | Remote (+1) | Ontario (+1)"
                        },
                        {
                            "id": 2,
                            "title": "AI Product Manager",
                            "company": "TechCorp Canada",
                            "location": "Ottawa,ON (Hybrid)",
                            "salary": "$80,000 - $95,000",
                            "description": "Seeking an AI PM to lead our educational technology initiatives...",
                            "is_remote": False,
                            "job_url": "https://example.com/job2",
                            "posted_date": datetime.now(),
                            "match_score": 8,
                            "match_reasoning": "Strong match: AI PM role (+4) | Excellent salary (+3) | Ontario (+1)"
                        },
                        {
                            "id": 3,
                            "title": "Learning & Development Specialist",
                            "company": "Global Training Co.",
                            "location": "Mississauga, ON",
                            "salary": "$55,000",
                            "description": "Join our L&D team to design and deliver training programs...",
                            "is_remote": True,
                            "job_url": "https://example.com/job3",
                            "posted_date": datetime.now(),
                            "match_score": 7,
                            "match_reasoning": "Good match: L&D role (+4) | Competitive salary (+2) | Ontario (+1)"
                        }
                    ]
                    st.success(f"✅ Found {len(st.session_state.jobs)} jobs (DEMO MODE)")
                else:
                    # Real mode: use job scraper
                    scraper = JobScraper()
                    jobs = scraper.scrape_jobs(
                        keywords=keywords,
                        location=location,
                        max_jobs=max_jobs,
                        job_type=job_type,
                        remote=remote
                    )
                    
                    # Score each job
                    resume_summary = "EdTech and L&D professional with AI/SaaS experience"
                    for job in jobs:
                        score_data = ai_agent.score_job(job, resume_summary)
                        job['match_score'] = score_data['score']
                        job['match_reasoning'] = score_data['reasoning']
                    
                    st.session_state.jobs = sorted(jobs, key=lambda x: x.get('match_score', 0), reverse=True)
                    st.success(f"✅ Found and scored {len(jobs)} jobs!")
                
                streamlit_logger.info(f"Job search completed: {keywords}")
            
            except Exception as e:
                st.error(f"Search failed: {e}")
                streamlit_logger.error(f"Job search error: {e}", exc_info=True)
    
    # Display jobs
    if st.session_state.jobs:
        st.markdown("---")
        st.markdown(f"### Results ({len(st.session_state.jobs)} jobs)")
        
        for job in st.session_state.jobs:
            score = job.get('match_score', 0)
            
            # Score badge color
            if score >= 8:
                badge_class = "score-high"
            elif score >= 5:
                badge_class = "score-medium"
            else:
                badge_class = "score-low"
            
            with st.container():
                cols = st.columns([3, 1])
                
                with cols[0]:
                    st.markdown(f"#### {job.get('title', 'Unknown')}")
                    st.markdown(f"**{job.get('company', 'Unknown')}** • {job.get('location', 'N/A')}")
                    st.markdown(f"💰 {job.get('salary', 'Not specified')} | 🏠 {'Remote' if job.get('is_remote') else 'On-site'}")
                    
                    with st.expander("📄 Description"):
                        st.write(job.get('description', 'No description')[:500] + "...")
                    
                    st.caption(f"🎯 **Match Reasoning:** {job.get('match_reasoning', 'N/A')}")
                
                with cols[1]:
                    st.markdown(f'<div class="score-badge {badge_class}">{score}/10</div>', unsafe_allow_html=True)
                    st.markdown("")
                    
                    if st.button("✏️ Optimize Resume", key=f"resume_{job.get('id', 0)}"):
                        st.info("Resume optimization will be available once AI module is connected!")
                    
                    if st.button("✉️ Create Draft", key=f"email_{job.get('id', 0)}"):
                        with st.spinner("Generating email..."):
                            email = ai_agent.generate_cold_email(job, "Hiring Manager", "initial")
                            st.text_area("Generated Email:", email, height=300)
                            st.success("Email generated! (Gmail integration coming soon)")
                
                st.markdown("---")

elif page == "📊 Dashboard":
    st.markdown('<h1 class="main-header">Application Dashboard 📊</h1>', unsafe_allow_html=True)
    
    st.info("📋 Application tracking will be available once database is connected")
    
    # Demo kanban board
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 📝 To Apply")
        st.metric("Jobs", 3)
    
    with col2:
        st.markdown("### ✉️ Sent")
        st.metric("Applications", 0)
    
    with col3:
        st.markdown("### 💬 Replied")
        st.metric("Responses", 0)
    
    with col4:
        st.markdown("### 📅 Interview")
        st.metric("Scheduled", 0)

elif page == "⚙️ Settings":
    st.markdown('<h1 class="main-header">Settings ⚙️</h1>', unsafe_allow_html=True)
    
    st.markdown("### API Configuration")
    
    with st.expander("🔑 API Keys Status"):
        st.write("**OpenAI:** ", "✅ Connected" if not st.session_state.demo_mode else "❌ Not configured")
        st.write("**Apify:** ", "❌ Not checked")
        st.write("**Gmail:** ", "❌ Not configured")
        st.write("**Database:** ", "❌ Not connected")
    
    st.markdown("### Job Search Preferences")
    
    default_keywords = st.text_area(
        "Default Keywords",
        value="Instructional Design, L&D, EdTech, AI PM, Automation",
        help="These keywords will be used by default in searches"
    )
    
    default_location = st.text_input(
        "Default Location",
        value="Ontario, Canada"
    )
    
    scraping_delay = st.slider(
        "Scraping Delay (seconds)",
        min_value=3,
        max_value=10,
        value=5,
        help="Delay between requests to avoid detection"
    )
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved!")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 2rem 0;'>
        <p>Job Autopilot 🚀 | Built with ❤️ and AI</p>
        <p><a href="https://github.com/Schlaflied/job-autopilot" target="_blank">GitHub</a></p>
    </div>
    """,
    unsafe_allow_html=True
)
