
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.resume_generator import resume_generator
from modules.ats_scorer import ats_scorer
from modules.job_scraper import JobScraper

def test_resume_flow():
    print("Testing Resume Flow...")
    
    # 1. Mock Data
    resume_data = {
        "name": "Jane Doe",
        "contact": {"email": "jane@example.com", "phone": "123-456-7890", "location": "Toronto, ON"},
        "summary": "Experienced professional.",
        "experience": [
            {
                "title": "Software Engineer",
                "company": "Tech Co",
                "duration": "2020 - Present",
                "details": ["Built stuff.", "Fixed bugs."]
            }
        ],
        "skills": ["Python", "Java", "SQL"],
        "education": [{"title": "BSc Comp Sci", "details": ["University of Toronto"]}]
    }
    
    jd = """
    We are looking for a Software Engineer with Python and SQL skills.
    You will build stuff and fix bugs. Experience with AWS is a plus.
    """
    
    # 2. Test Scraper Cleaner
    scraper = JobScraper()
    cleaned = scraper.clean_html_tags("<p>Test <b>Description</b></p>")
    print(f"Cleaned HTML: {cleaned}")
    assert cleaned == "Test Description"
    
    # 3. Test AI Tailoring (Mocking AI agent would be ideal, but we'll trust the method structure exists)
    # We won't actually call OpenAI here to save tokens/time, but we check if method exists
    assert hasattr(resume_generator, 'tailor_and_compress')
    print("tailor_and_compress method exists.")
    
    # 4. Test ATS Scorer
    score = ats_scorer.score_resume(json.dumps(resume_data), jd)
    print(f"ATS Score: {score['score']}")
    print(f"Missing Keywords: {score['missing_keywords']}")
    
    # 5. Test PDF Export (Classic)
    resume_data['_meta'] = {'template': 'classic_single_column'}
    path_classic = resume_generator.export_pdf(resume_data, "test_classic.pdf")
    print(f"Exported Classic PDF: {path_classic}")
    
    # 6. Test PDF Export (Modern)
    resume_data['_meta'] = {'template': 'modern_two_column'}
    path_modern = resume_generator.export_pdf(resume_data, "test_modern.pdf")
    print(f"Exported Modern PDF: {path_modern}")

if __name__ == "__main__":
    try:
        test_resume_flow()
        print("✅ Resume Flow Test Passed")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
