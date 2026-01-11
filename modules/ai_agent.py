# Job Autopilot - AI Agent
# GPT-4o-mini for job scoring, resume optimization, and email generation

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from modules.logger_config import app_logger

load_dotenv()

class AIAgent:
    """AI-powered job matching, resume optimization, and email generation"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            app_logger.warning("OPENAI_API_KEY not found - running in DEMO mode")
            self.demo_mode = True
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            self.demo_mode = False
            app_logger.info("OpenAI client initialized")
        
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def score_job(self, job_data: Dict, resume_summary: str) -> Dict:
        """
        Score job based on matching criteria (0-10 scale)
        
        Args:
            job_data: Job details dict
            resume_summary: User's resume summary
        
        Returns:
            dict: {"score": int, "reasoning": str}
        """
        if self.demo_mode:
            return self._demo_score_job(job_data)
        
        try:
            prompt = f"""
You are an intelligent job matching system. Rate this job from 0-10 based on the candidate's profile.

Scoring Criteria:
- EdTech/L&D/Instructional Design field: 4 points
- AI PM/AI application/Automation/Workflow roles: 4 points
- Salary >$25/hr or $50,080/year or $4,800/month: 3 points
- Remote position: 1 point
- Keywords (System Implementation, Pilot Program, Workflow Automation, POC): 1 point
- Benefits offered: 1 point
- Full-time position: 1 point
- Ontario, Canada location: 1 point

Total: 10 points maximum

Job Details:
Title: {job_data.get('title', '')}
Company: {job_data.get('company', '')}
Location: {job_data.get('location', '')}
Salary: {job_data.get('salary', 'Not specified')}
Remote: {job_data.get('is_remote', False)}
Description: {job_data.get('description', '')[:500]}

Candidate Profile:
{resume_summary}

Provide your response in JSON format:
{{"score": <0-10>, "reasoning": "<brief explanation>"}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a job matching expert."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            app_logger.info(f"Job scored: {job_data.get('title')} - {result['score']}/10")
            return result
        
        except Exception as e:
            app_logger.error(f"Job scoring failed: {e}", exc_info=True)
            return {"score": 5, "reasoning": "Error during scoring"}
    
    def _demo_score_job(self, job_data: Dict) -> Dict:
        """Demo mode scoring based on keywords"""
        title = job_data.get('title', '').lower()
        description = job_data.get('description', '').lower()
        
        score = 0
        reasons = []
        
        # Check category
        if any(kw in title + description for kw in ['instructional', 'edtech', 'learning', 'training']):
            score += 4
            reasons.append("EdTech/L&D role (+4)")
        elif any(kw in title + description for kw in ['ai', 'automation', 'workflow']):
            score += 4
            reasons.append("AI/Automation role (+4)")
        
        # Salary check
        salary_text = job_data.get('salary', '').lower()
        if any(indicator in salary_text for indicator in ['$50', '$60', '$70', '$80']):
            score += 3
            reasons.append("Good salary (+3)")
        
        # Remote
        if job_data.get('is_remote'):
            score += 1
            reasons.append("Remote (+1)")
        
        # Location
        location = job_data.get('location', '').lower()
        if 'ontario' in location or 'canada' in location:
            score += 1
            reasons.append("Ontario location (+1)")
        
        return {
            "score": min(score, 10),
            "reasoning": " | ".join(reasons) if reasons else "General match"
        }
    
    def optimize_resume(self, resume_data: Dict, job_description: str) -> Dict:
        """
        Optimize resume for specific job (1-page constraint)
        
        Args:
            resume_data: Current resume dict
            job_description: Job description text
        
        Returns:
            dict: Optimized resume data
        """
        if self.demo_mode:
            app_logger.info("DEMO mode: Resume optimization skipped")
            return resume_data
        
        try:
            prompt = f"""
Optimize this resume for the following job, compressed to fit on exactly 1 page:

CONSTRAINTS:
- Maximum 600 words
- Font: Arial 11pt
- Margins: 0.5 inch
- Must fit on 1 page

OPTIMIZATION TASKS:
1. Tailor Professional Summary to highlight relevant skills
2. Keep only the most relevant 2-3 experiences
3. Select top 10 skills matching the job
4. Include top 3 projects relevant to this role
5. Education in 1 line

Job Description:
{job_description[:800]}

Current Resume:
{resume_data}

Return optimized resume in the SAME JSON structure with condensed content.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional resume writer specializing in ATS optimization."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            
            import json
            optimized = json.loads(response.choices[0].message.content)
            app_logger.info("Resume optimized successfully")
            return optimized
        
        except Exception as e:
            app_logger.error(f"Resume optimization failed: {e}", exc_info=True)
            return resume_data
    
    def generate_cold_email(
        self,
        job_data: Dict,
        hr_name: str = "Hiring Manager",
        stage: str = "initial"
    ) -> str:
        """
        Generate cold email (two-stage strategy)
        
        Args:
            job_data: Job details
            hr_name: HR contact name
            stage: "initial" or "followup"
        
        Returns:
            str: Email content
        """
        if self.demo_mode:
            return self._demo_email(job_data, hr_name, stage)
        
        try:
            if stage == "initial":
                prompt = f"""
Generate a cold email for this job (Stage 1: NO resume attachment).

Requirements:
- Length: <150 words
- Tone: Professional but personable
- Include: 1 relevant project/skill match
- Ask if they'd like to see full resume
- Add AI disclosure: "Full disclosure: This initial outreach was drafted by my AI assistant to save you time, but I'm a real person eager to discuss..."
- End with portfolio link: https://syttt.my.canva.site/

Job:
Title: {job_data.get('title')}
Company: {job_data.get('company')}
Description: {job_data.get('description', '')[:300]}

Candidate background: EdTech/L&D professional with AI/SaaS experience (Academic Compass, Project Lens projects)

Return only the email body (no subject line).
"""
            else:  # followup
                prompt = f"""
Generate a follow-up email (Stage 2: WITH resume attachment).

Context: HR replied positively to initial contact.

Requirements:
- Thank them for reply
- Attach resume (mention "attached")
- Suggest meeting/call times
- Length: <200 words

Job: {job_data.get('title')} at {job_data.get('company')}

Return only the email body.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional cold email writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            email_body = response.choices[0].message.content
            app_logger.info(f"Generated {stage} email for {job_data.get('title')}")
            return email_body
        
        except Exception as e:
            app_logger.error(f"Email generation failed: {e}", exc_info=True)
            return self._demo_email(job_data, hr_name, stage)
    
    def _demo_email(self, job_data: Dict, hr_name: str, stage: str) -> str:
        """Demo email template"""
        if stage == "initial":
            return f"""Hi {hr_name},

I noticed the {job_data.get('title')} opening at {job_data.get('company')} and was immediately drawn to the opportunity.

I recently built an AI-powered career tool using GPT-4o-mini that scored this role 9/10 for my background in EdTech and L&D automation.

Full disclosure: This initial outreach was drafted by my AI assistant to save you time, but I'm a real person eager to discuss how my experience with AI-driven learning tools can contribute to your team.

Would you be open to a brief conversation? I'd love to share my portfolio: https://syttt.my.canva.site/

Best regards,
Yuting Sun"""
        else:
            return f"""Hi {hr_name},

Thank you for your response! I'm excited about the {job_data.get('title')} opportunity.

I've attached my tailored resume highlighting my experience with instructional design, AI integration, and learning platform development.

I'm available for a call this week - would Tuesday or Thursday afternoon work for you?

Looking forward to discussing how I can contribute to {job_data.get('company')}.

Best,
Yuting Sun"""

# Global AI agent instance
ai_agent = AIAgent()

if __name__ == "__main__":
    # Test in demo mode
    test_job = {
        "title": "Instructional Designer",
        "company": "EdTech Corp",
        "description": "Looking for an instructional designer with AI experience",
        "location": "Ontario, Canada",
        "is_remote": True,
        "salary": "$60,000"
    }
    
    result = ai_agent.score_job(test_job, "EdTech professional")
    print(f"Score: {result['score']}/10")
    print(f"Reason: {result['reasoning']}")
    
    email = ai_agent.generate_cold_email(test_job, "Sarah", "initial")
    print(f"\nEmail:\n{email}")
