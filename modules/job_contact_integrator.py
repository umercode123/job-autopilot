"""
Job Scraper + Coffee Chat Integration
Links high-scoring jobs with LinkedIn alumni search
"""
import os
import sys
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database import Job, SessionLocal
from modules.coffee_chat_models import CoffeeChatContact, UserProfile

load_dotenv()


class JobContactIntegrator:
    """
    Integrates job scraper with coffee chat contact finder
    """
    
    def __init__(self):
        self.session = SessionLocal()
    
    def get_high_value_jobs(
        self, 
        days: int = 7, 
        min_score: int = 7,
        limit: Optional[int] = None
    ) -> List[Job]:
        """
        Get recent jobs with high AI match scores
        
        Args:
            days: Look back N days
            min_score: Minimum match_score (default: 7/10)
            limit: Max number of jobs to return
            
        Returns:
            List of Job objects sorted by score
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.session.query(Job).filter(
            Job.match_score >= min_score,
            Job.created_at >= cutoff_date
        ).order_by(
            Job.match_score.desc(),  # Highest score first
            Job.created_at.desc()     # Most recent first
        )
        
        if limit:
            query = query.limit(limit)
        
        jobs = query.all()
        
        print(f"📥 Found {len(jobs)} high-value jobs (score ≥ {min_score})")
        
        return jobs
    
    def group_jobs_by_domain(self, jobs: List[Job]) -> Dict[str, List[Job]]:
        """
        Group jobs by company domain
        
        Args:
            jobs: List of Job objects
            
        Returns:
            Dict mapping domain -> list of jobs
        """
        # Separate jobs with domain vs without
        jobs_with_domain = {}
        jobs_without_domain = {}
        
        for job in jobs:
            if job.company_domain:
                domain = job.company_domain
                if domain not in jobs_with_domain:
                    jobs_with_domain[domain] = []
                jobs_with_domain[domain].append(job)
            else:
                # Group by company name for jobs without domain
                company = job.company
                if company not in jobs_without_domain:
                    jobs_without_domain[company] = []
                jobs_without_domain[company].append(job)
        
        print(f"\n📊 Job grouping:")
        print(f"   Companies with domain: {len(jobs_with_domain)}")
        print(f"   Companies without domain: {len(jobs_without_domain)}")
        
        return {
            'with_domain': jobs_with_domain,
            'without_domain': jobs_without_domain
        }
    
    def get_companies_for_search(
        self, 
        days: int = 7, 
        min_score: int = 7
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Get companies to search for alumni
        Returns two lists: companies with domains, companies without
        
        Args:
            days: Look back N days
            min_score: Minimum job score
            
        Returns:
            Tuple of (companies_with_domain, companies_without_domain)
            Each company dict contains:
                - domain/name: Company identifier
                - jobs: List of Job objects
                - best_score: Highest match_score among jobs
                - job_count: Number of jobs at this company
        """
        # Get high-value jobs
        jobs = self.get_high_value_jobs(days=days, min_score=min_score)
        
        if not jobs:
            print("⚠️ No high-value jobs found")
            return [], []
        
        # Group by domain/company
        grouped = self.group_jobs_by_domain(jobs)
        
        # Process companies with domain
        companies_with_domain = []
        for domain, job_list in grouped['with_domain'].items():
            best_job = max(job_list, key=lambda j: j.match_score)
            companies_with_domain.append({
                'domain': domain,
                'company_name': best_job.company,
                'jobs': job_list,
                'best_score': best_job.match_score,
                'job_count': len(job_list),
                'has_domain': True
            })
        
        # Process companies without domain
        companies_without_domain = []
        for company, job_list in grouped['without_domain'].items():
            best_job = max(job_list, key=lambda j: j.match_score)
            companies_without_domain.append({
                'domain': None,
                'company_name': company,
                'jobs': job_list,
                'best_score': best_job.match_score,
                'job_count': len(job_list),
                'has_domain': False
            })
        
        # Sort by best score
        companies_with_domain.sort(key=lambda c: c['best_score'], reverse=True)
        companies_without_domain.sort(key=lambda c: c['best_score'], reverse=True)
        
        return companies_with_domain, companies_without_domain
    
    def print_company_summary(
        self, 
        companies_with_domain: List[Dict],
        companies_without_domain: List[Dict]
    ):
        """
        Print summary of companies to search
        """
        print("\n" + "=" * 60)
        print("Companies to Search for Alumni")
        print("=" * 60)
        
        if companies_with_domain:
            print(f"\n🔑 With Domain ({len(companies_with_domain)} companies):")
            print("-" * 60)
            for i, company in enumerate(companies_with_domain[:10], 1):
                print(f"{i:2d}. {company['company_name']:<30} ({company['domain']})")
                print(f"    Score: {company['best_score']}/10 | Jobs: {company['job_count']}")
        
        if companies_without_domain:
            print(f"\n⚠️ Without Domain ({len(companies_without_domain)} companies):")
            print("-" * 60)
            for i, company in enumerate(companies_without_domain[:5], 1):
                print(f"{i:2d}. {company['company_name']:<30}")
                print(f"    Score: {company['best_score']}/10 | Jobs: {company['job_count']}")
    
    def save_contact_with_job_link(
        self, 
        contact_data: Dict,
        job: Job,
        priority_score: int
    ) -> CoffeeChatContact:
        """
        Save contact to database with job linkage
        
        Args:
            contact_data: Contact information from LinkedIn
            job: Related Job object
            priority_score: Calculated priority score
            
        Returns:
            CoffeeChatContact object
        """
        # Check if contact already exists
        existing = self.session.query(CoffeeChatContact).filter_by(
            linkedin_url=contact_data['linkedin_url']
        ).first()
        
        if existing:
            print(f"   Contact already exists: {contact_data['name']}")
            return existing
        
        # Create new contact
        contact = CoffeeChatContact(
            name=contact_data['name'],
            linkedin_url=contact_data['linkedin_url'],
            current_company=contact_data.get('company', job.company),
            current_title=contact_data.get('title', ''),
            
            # Job linkage
            related_job_id=job.id,
            job_match_score=job.match_score,
            has_active_posting=True,
            
            # Contact metadata
            connection_degree=contact_data.get('connection_degree', '2nd'),
            is_alumni=contact_data.get('is_alumni', True),
            school_name=contact_data.get('school_name', ''),
            
            # Priority
            priority_score=priority_score,
            
            # Status
            status='pending',
            connection_sent_at=None,
            
            # Timestamps
            discovered_at=datetime.utcnow()
        )
        
        self.session.add(contact)
        self.session.commit()
        
        return contact
    
    def close(self):
        """Close database session"""
        self.session.close()


# Usage example
if __name__ == "__main__":
    integrator = JobContactIntegrator()
    
    try:
        # Get companies to search
        with_domain, without_domain = integrator.get_companies_for_search(
            days=7,
            min_score=7
        )
        
        # Print summary
        integrator.print_company_summary(with_domain, without_domain)
        
        print("\n✅ Ready to search LinkedIn for alumni at these companies!")
        
    finally:
        integrator.close()
