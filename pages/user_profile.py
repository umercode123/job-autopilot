"""
User Profile Configuration Page
"""
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified
import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.coffee_chat_models import UserProfile

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="User Profile - Coffee Chat",
    page_icon="👤",
    layout="wide"
)

# Database connection
@st.cache_resource
def get_db_session():
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

session = get_db_session()

# Page title
st.title("👤 User Profile")
st.markdown("Configure your schools, target fields, and daily limits")

# Get or create user profile
profile = session.query(UserProfile).first()
if not profile:
    profile = UserProfile()
    session.add(profile)
    session.commit()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Schools Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.header("🎓 Your Schools")
st.warning("⚠️ **Important**: Only Canadian schools/colleges supported (must be searchable on Google)")

# Display existing schools
if profile.schools:
    st.subheader("Configured Schools")
    
    for i, school in enumerate(profile.schools):
        with st.expander(
            f"🎓 {school['name']} (Priority: {school.get('priority', 'N/A')})",
            expanded=False
        ):
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**Degree:** {school.get('degree', 'N/A')}")
                st.write(f"**Graduation Year:** {school.get('graduation_year', 'N/A')}")
            
            with col2:
                st.write(f"**Priority:** {school.get('priority', 'N/A')}")
                st.caption("(1 = highest priority)")
            
            with col3:
                if st.button("🗑️ Remove", key=f"remove_school_{i}"):
                    profile.schools.pop(i)
                    flag_modified(profile, 'schools')  # Tell SQLAlchemy the list changed
                    session.commit()
                    st.rerun()
else:
    st.info("No schools configured. Please add below.")

# Add new school
st.subheader("Add New School")

with st.form("add_school_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        school_name = st.text_input(
            "School Name *",
            placeholder="University of Western Ontario",
            help="Must be a Canadian University or College"
        )
        degree = st.text_input(
            "Degree",
            placeholder="Master's / BA / Diploma",
            help="e.g., Master's, BA, MBA, Diploma"
        )
    
    with col2:
        graduation_year = st.number_input(
            "Graduation Year",
            min_value=2000,
            max_value=2030,
            value=2024,
            help="Year you graduated from this school"
        )
        priority = st.number_input(
            "Priority *",
            min_value=1,
            max_value=10,
            value=len(profile.schools) + 1 if profile.schools else 1,
            help="1 = highest priority (recent graduate school first)"
        )
    
    # Submit button
    col_submit, col_help = st.columns([1, 3])
    with col_submit:
        submit_school = st.form_submit_button("➕ Add School", use_container_width=True)
    
    with col_help:
        st.caption("💡 Tip: Set recent graduate school as priority 1")

if submit_school:
    if school_name:
        # TODO: Add Google validation (Phase 2)
        new_school = {
            "name": school_name.strip(),
            "degree": degree.strip() if degree else "N/A",
            "graduation_year": graduation_year,
            "priority": priority
        }
        
        if not profile.schools:
            profile.schools = []
        
        profile.schools.append(new_school)
        flag_modified(profile, 'schools')  # Tell SQLAlchemy the list changed
        session.commit()
        st.success(f"✅ Added: {school_name}")
        st.rerun()
    else:
        st.error("❌ Please enter school name")

st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Target Fields Tags
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.header("🏷️ Target Fields")
st.caption("Add up to 5 target fields (e.g., Learning & Development, HR, AI)")

if profile.target_fields and len(profile.target_fields) >= 5:
    st.warning("⚠️ Maximum 5 fields allowed. Remove a field to add more.")

# Display existing tags
if profile.target_fields:
    st.subheader("Current Fields")
    
    # Display tags in columns
    cols = st.columns(min(len(profile.target_fields), 4))
    
    for i, field in enumerate(profile.target_fields):
        with cols[i % 4]:
            col_tag, col_remove = st.columns([3, 1])
            with col_tag:
                st.button(f"🏷️ {field}", disabled=True, use_container_width=True)
            with col_remove:
                if st.button("❌", key=f"remove_field_{i}"):
                    profile.target_fields.pop(i)
                    flag_modified(profile, 'target_fields')  # Tell SQLAlchemy the list changed
                    session.commit()
                    st.rerun()
else:
    st.info("No field tags added yet")

# Add new field
with st.form("add_field_form"):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_field = st.text_input(
            "Add New Field",
            placeholder="e.g., Learning & Development",
            help="Enter your target field"
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        submit_field = st.form_submit_button("➕ Add", use_container_width=True)

if submit_field:
    if new_field:
        new_field = new_field.strip()
        
        if not profile.target_fields:
            profile.target_fields = []
        
        # Check max 5 fields limit
        if len(profile.target_fields) >= 5:
            st.error("❌ Maximum 5 fields allowed. Remove a field first.")
        elif new_field not in profile.target_fields:
            profile.target_fields.append(new_field)
            flag_modified(profile, 'target_fields')  # Tell SQLAlchemy the list changed
            session.commit()
            st.success(f"✅ Added: {new_field}")
            st.rerun()
        else:
            st.warning(f"⚠️ {new_field} already exists")
    else:
        st.error("❌ Please enter field name")

# Smart suggested tags based on first field
st.caption("**Suggested Fields** (smart suggestions based on your fields):")

# Generate smart suggestions
def get_smart_suggestions(current_fields):
    """
    Generate smart field suggestions based on user's first field
    """
    all_suggestions = {
        "Learning & Development": [
            "Instructional Design",
            "Training & Development",
            "Education Technology",
            "HR / People Operations",
            "Talent Development"
        ],
        "HR": [
            "People Operations",
            "Talent Acquisition",
            "Learning & Development",
            "Employee Experience",
            "Organizational Development"
        ],
        "AI": [
            "Machine Learning",
            "Data Science",
            "NLP",
            "Computer Vision",
            "MLOps"
        ],
        "Product Management": [
            "Product Design",
            "UX Research",
            "Product Marketing",
            "Agile",
            "Product Strategy"
        ],
        "Data Science": [
            "Machine Learning",
            "AI",
            "Data Engineering",
            "Analytics",
            "Business Intelligence"
        ]
    }
    
    # Default suggestions if no fields or no match
    default = [
        "Learning & Development",
        "HR / People Operations",
        "AI / Machine Learning",
        "Product Management",
        "Data Science",
        "UX Design",
        "Education Technology",
        "Training & Development",
        "Instructional Design"
    ]
    
    if not current_fields:
        return default
    
    # Get suggestions based on first field
    first_field = current_fields[0]
    
    # Try to match first field with keys
    for key in all_suggestions:
        if key.lower() in first_field.lower() or first_field.lower() in key.lower():
            return all_suggestions[key] + default
    
    return default

suggested_fields = get_smart_suggestions(profile.target_fields)

if len(profile.target_fields) < 5:  # Only show suggestions if under limit
    cols = st.columns(3)
    suggestion_count = 0
    
    for i, suggested in enumerate(suggested_fields):
        if profile.target_fields and suggested in profile.target_fields:
            continue  # Skip if already added
        
        if suggestion_count >= 9:  # Show max 9 suggestions
            break
        
        with cols[suggestion_count % 3]:
            if st.button(f"+ {suggested}", key=f"suggest_{i}", use_container_width=True):
                if not profile.target_fields:
                    profile.target_fields = []
                
                if len(profile.target_fields) < 5:
                    profile.target_fields.append(suggested)
                    flag_modified(profile, 'target_fields')  # Tell SQLAlchemy the list changed
                    session.commit()
                    st.rerun()
                else:
                    st.error("Maximum 5 fields reached")
        
        suggestion_count += 1
else:
    st.info("✓ Maximum 5 fields reached. Remove a field to add more.")

st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Daily Limits and Geographic Settings
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.header("⚙️ Settings")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("⏰ Daily Limits")
    st.caption("Conservative settings to avoid LinkedIn bans")
    
    daily_connections = st.number_input(
        "LinkedIn Connections / day",
        min_value=1,
        max_value=50,
        value=profile.daily_connection_limit,
        help="Recommended: 20 (conservative)"
    )
    
    daily_messages = st.number_input(
        "LinkedIn Messages / day",
        min_value=1,
        max_value=50,
        value=profile.daily_message_limit,
        help="Recommended: 10 (conservative)"
    )

with col2:
    st.subheader("🌍 Target Location")
    st.caption("Geographic targeting")
    
    target_location = st.selectbox(
        "Location",
        options=["Canada"],
        index=0,
        disabled=True,
        help="Currently only Canada supported"
    )
    
    st.info("✓ Canada only (for work visa)")

with col3:
    st.subheader("📊 Current Config")
    st.metric("Schools", len(profile.schools) if profile.schools else 0)
    st.metric("Fields", len(profile.target_fields) if profile.target_fields else 0)
    st.metric("Daily Cap", f"{daily_connections + daily_messages} actions")

st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Save Button
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
col_save, col_status = st.columns([1, 3])

with col_save:
    if st.button("💾 Save Profile", type="primary", use_container_width=True):
        profile.daily_connection_limit = daily_connections
        profile.daily_message_limit = daily_messages
        profile.target_location = target_location
        session.commit()
        st.success("✅ Profile saved!")
        st.balloons()

with col_status:
    if not profile.schools:
        st.warning("⚠️ Please add at least one school")
    elif not profile.target_fields:
        st.warning("⚠️ Please add at least one field")
    else:
        st.success("✅ Profile complete! Ready to use Coffee Chat Finder")
        
        # Navigate to Coffee Chat Center
        st.success("☕ **Next Step:** Click 'coffee_chat_center' in the sidebar to start! →")

# Debug info (optional)
with st.expander("🔍 Debug Info (Development)"):
    st.json({
        "schools": profile.schools,
        "target_fields": profile.target_fields,
        "daily_connection_limit": profile.daily_connection_limit,
        "daily_message_limit": profile.daily_message_limit,
        "target_location": profile.target_location
    })
