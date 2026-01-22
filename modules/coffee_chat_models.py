"""
Coffee Chat Database Models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class UserProfile(Base):
    """
    User configuration profile
    """
    __tablename__ = 'user_profiles'
    
    id = Column(Integer, primary_key=True)
    
    # Schools configuration (JSON array)
    schools = Column(JSON, default=list)
    # Example: [
    #   {"name": "University of Western Ontario", "degree": "Master's", "graduation_year": 2024, "priority": 1},
    #   {"name": "York University", "degree": "BA", "graduation_year": 2021, "priority": 2}
    # ]
    
    # Target fields (JSON array)
    target_fields = Column(JSON, default=list)
    # Example: ["Learning & Development", "HR", "AI"]
    
    # Daily limits
    daily_connection_limit = Column(Integer, default=20)
    daily_message_limit = Column(Integer, default=10)
    
    # Geographic restriction
    target_location = Column(String, default='Canada')
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CoffeeChatContact(Base):
    """
    Coffee Chat contact information
    """
    __tablename__ = 'coffee_chat_contacts'
    
    id = Column(Integer, primary_key=True)
    
    # Basic information
    name = Column(String, nullable=False)
    company = Column(String)
    company_domain = Column(String)  # For Apollo domain matching
    company_linkedin_url = Column(String)
    title = Column(String)
    linkedin_url = Column(String, unique=True)  # LinkedIn profile URL
    
    # Classification
    is_alumni = Column(Boolean, default=False)
    alumni_school = Column(String)  # Which school alumni
    school_priority = Column(Integer)  # School priority level
    
    is_potential_supervisor = Column(Boolean, default=False)
    is_existing_connection = Column(Boolean, default=False)  # Already a LinkedIn connection
    
    # Priority scoring
    priority_score = Column(Float, default=0.0)
    priority_reasoning = Column(Text)  # AI scoring reasoning
    
    # LinkedIn activity analysis
    linkedin_last_activity = Column(DateTime)
    linkedin_activity_summary = Column(Text)  # AI analyzed activity summary
    
    # LinkedIn Connection status
    connection_sent_at = Column(DateTime)
    connection_accepted_at = Column(DateTime)
    connection_followup_sent_at = Column(DateTime)
    connection_followup_count = Column(Integer, default=0)
    connection_status = Column(String, default='not_sent')  
    # 'not_sent', 'pending', 'accepted', 'rejected', 'timeout'
    
    # LinkedIn message status
    message_sent_at = Column(DateTime)
    message_content = Column(Text)  # AI generated message content
    message_followup_sent_at = Column(DateTime)
    message_followup_count = Column(Integer, default=0)
    replied_at = Column(DateTime)
    reply_content = Column(Text)
    
    # Apollo email fallback
    email = Column(String)
    email_sent_at = Column(DateTime)
    email_content = Column(Text)
    email_source = Column(String)  # 'apollo_verified', 'not_found', 'manual'
    email_reply_at = Column(DateTime)
    
    # Overall status
    status = Column(String, default='new')  
    # 'new' → 'connection_sent' → 'connected' → 'message_sent' → 'replied' → 'scheduled' → 'completed'
    # or 'given_up'
    
    # Scam detection
    scam_risk_score = Column(Float, default=0.0)
    scam_reasons = Column(JSON)  # List of scam risk reasons
    is_verified_safe = Column(Boolean, default=False)
    
    # Job posting association
    has_active_posting = Column(Boolean, default=False)
    related_job_ids = Column(JSON)  # Related job posting IDs
    
    # Give-up mechanism
    suggested_give_up = Column(Boolean, default=False)
    give_up_reason = Column(String)
    give_up_confidence = Column(Float)  # AI suggested give-up confidence (0-100)
    
    # Next action
    next_action = Column(String)  # 'send_connection', 'send_message', 'follow_up', 'wait', 'give_up'
    next_action_date = Column(DateTime)  # Next action date
    
    # AI memory related
    interaction_count = Column(Integer, default=0)
    success_pattern = Column(String)  # 'quick_responder', 'slow_responder', 'unresponsive'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<CoffeeChatContact(name='{self.name}', company='{self.company}', status='{self.status}')>"


class CoffeeChatInteraction(Base):
    """
    Specific interaction records (for AI learning)
    """
    __tablename__ = 'coffee_chat_interactions'
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, nullable=False)  # Link to CoffeeChatContact
    
    action_type = Column(String, nullable=False)  # 'connection', 'message', 'email', 'follow_up'
    action_content = Column(Text)
    
    result = Column(String)  # 'success', 'pending', 'failed', 'ignored'
    result_details = Column(JSON)
    
    # AI decision record
    ai_decision = Column(JSON)  # AI decision process and reasoning
    ai_confidence = Column(Float)
    
    timestamp = Column(DateTime, default=datetime.now)
