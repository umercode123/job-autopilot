"""
Job Autopilot - Coffee Chat Automation
Main Home Page
"""
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Job Autopilot - Coffee Chat",
    page_icon="🚀",
    layout="wide"
)

# Header
st.title("🚀 Job Autopilot - Coffee Chat Automation")
st.markdown("### AI-powered networking to bypass ATS and land your dream job")

st.divider()

# Introduction
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## Welcome! 👋
    
    This system helps you:
    - ✅ **Find alumni** from your schools at target companies
    - ✅ **Connect with potential supervisors** in your field
    - ✅ **Send personalized coffee chat messages** using AI
    - ✅ **Track engagement** and optimize your outreach
    - ✅ **Bypass ATS** by building direct connections
    
    ### Why Coffee Chats?
    
    According to career coaches, **80% of jobs are filled through networking**.
    Traditional applications often get filtered by ATS before reaching humans.
    
    **Coffee chats** help you:
    - Build authentic relationships
    - Learn about company culture
    - Get internal referrals
    - Stand out from other candidates
    """)

with col2:
    st.info("""
    **📊 Success Rate**
    
    With this system:
    - 25-35% connection acceptance
    - 15-20% coffee chat replies
    - 5-10% referrals
    
    **🎯 Conservative Strategy**
    
    - Max 20 connections/day
    - Max 10 messages/day
    - Smart AI personalization
    - Graceful give-up mechanism
    """)

st.divider()

# Quick start guide
st.header("🚀 Getting Started")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1️⃣ Configure Profile")
    st.write("Set up your schools, target fields, and daily limits")
    
    if st.button("📝 User Profile", use_container_width=True, type="primary"):
        st.switch_page("pages/user_profile.py")

with col2:
    st.subheader("2️⃣ Find Contacts")
    st.write("Search LinkedIn for alumni and professionals")
    
    if st.button("☕ Coffee Chat Center", use_container_width=True):
        st.switch_page("pages/coffee_chat_center.py")

with col3:
    st.subheader("3️⃣ Track Progress")
    st.write("Monitor your outreach and success rates")
    
    if st.button("📊 Dashboard", use_container_width=True, disabled=True):
        st.info("Coming soon!")

st.divider()

# Architecture info
with st.expander("🏗️ Technical Architecture"):
    st.markdown("""
    ### Built with cutting-edge AI technologies:
    
    - **LangChain**: LLM orchestration
    - **crewAI**: Multi-agent collaboration
    - **chrome-devtools MCP**: LinkedIn automation
    - **Pinecone/Chroma**: Vector memory for AI learning
    - **PostgreSQL/SQLite**: Reliable data storage
    - **Streamlit**: Beautiful, responsive UI
    
    ### MCP 3-Layer Architecture:
    
    1. **Memory Layer**: Learns from past interactions
    2. **Decision Layer**: Smart next-action recommendations
    3. **Tool Layer**: LinkedIn, Apollo, Email automation
    """)

# Footer
st.divider()
st.caption("💡 **Tip**: Start by configuring your User Profile, then head to Coffee Chat Center")
st.caption("Built with ❤️ using AI")
