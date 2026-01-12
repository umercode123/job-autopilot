# Job Autopilot - Auto Follow-up Service
# Checks for Gmail replies and generates follow-up emails

import os
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv
from modules.database import SessionLocal, Application
from modules.ai_agent import ai_agent
from modules.logger_config import gmail_logger

load_dotenv()

class AutoFollowupService:
    """
    Automatically follow up on cold emails after N days if no reply
    
    Strategy:
    - Wait 3-5 days after initial email sent
    - If no HR reply detected, generate follow-up draft
    - Max 1 follow-up per application (不spam)
    """
    
    def __init__(self):
        self.followup_delay_days = int(os.getenv("FOLLOWUP_DELAY_DAYS", 5))
        self.max_followups = int(os.getenv("MAX_FOLLOWUPS_PER_JOB", 1))
        gmail_logger.info("Auto follow-up service initialized")
    
    def check_and_create_followups(self) -> List[Dict]:
        """
        Check all applications waiting for follow-up
        
        Returns:
            list: Applications that need follow-up
        """
        db = SessionLocal()
        followups_created = []
        
        try:
            # Find applications that:
            # 1. Initial email was sent
            # 2. No reply received
            # 3. Sent more than X days ago
            # 4. Haven't sent follow-up yet
            
            cutoff_date = datetime.utcnow() - timedelta(days=self.followup_delay_days)
            
            candidates = db.query(Application).filter(
                Application.email_stage == 'initial_sent',
                Application.hr_replied == False,
                Application.sent_at <= cutoff_date,
                Application.sent_at.isnot(None)
            ).all()
            
            gmail_logger.info(f"Found {len(candidates)} applications for follow-up check")
            
            for app in candidates:
                try:
                    # Generate follow-up email
                    job = app.job
                    hr_contact = app.hr_contact
                    
                    if not job or not hr_contact:
                        continue
                    
                    job_data = {
                        "title": job.title,
                        "company": job.company,
                        "description": job.description
                    }
                    
                    # Generate AI follow-up email
                    followup_email = ai_agent.generate_cold_email(
                        job_data=job_data,
                        hr_name=hr_contact.name or "Hiring Manager",
                        stage="followup"
                    )
                    
                    followups_created.append({
                        "application_id": app.id,
                        "job_title": job.title,
                        "company": job.company,
                        "hr_email": hr_contact.email,
                        "hr_name": hr_contact.name,
                        "email_content": followup_email,
                        "days_since_initial": (datetime.utcnow() - app.sent_at).days
                    })
                    
                    # Update application status
                    app.email_stage = 'followup_ready'
                    app.notes = f"Auto-generated follow-up on {datetime.utcnow().strftime('%Y-%m-%d')}"
                    
                    gmail_logger.info(f"Follow-up created for: {job.title} @ {job.company}")
                
                except Exception as e:
                    gmail_logger.error(f"Failed to create follow-up for app {app.id}: {e}")
                    continue
            
            db.commit()
            gmail_logger.info(f"Created {len(followups_created)} follow-up drafts")
            
        except Exception as e:
            db.rollback()
            gmail_logger.error(f"Follow-up check failed: {e}", exc_info=True)
        
        finally:
            db.close()
        
        return followups_created
    
    def get_followup_statistics(self) -> Dict:
        """Get follow-up statistics"""
        db = SessionLocal()
        
        try:
            stats = {
                "waiting_for_reply": db.query(Application).filter(
                    Application.email_stage == 'initial_sent',
                    Application.hr_replied == False
                ).count(),
                "followup_ready": db.query(Application).filter(
                    Application.email_stage == 'followup_ready'
                ).count(),
                "followup_sent": db.query(Application).filter(
                    Application.email_stage == 'followup_sent'
                ).count(),
                "received_replies": db.query(Application).filter(
                    Application.hr_replied == True
                ).count()
            }
            return stats
        
        finally:
            db.close()

# Global instance
auto_followup_service = AutoFollowupService()

if __name__ == "__main__":
    # Test
    results = auto_followup_service.check_and_create_followups()
    print(f"Follow-ups created: {len(results)}")
    
    stats = auto_followup_service.get_followup_statistics()
    print(f"Statistics: {stats}")
