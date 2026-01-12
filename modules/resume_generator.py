# Job Autopilot - Resume Generator
# AI-powered resume tailoring with ATS optimization

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from modules.ai_agent import ai_agent
from modules.logger_config import app_logger

load_dotenv()

class ResumeGenerator:
    """
    Generate ATS-optimized resumes tailored to job descriptions
    
    Features:
    - AI-powered keyword extraction from JD
    - Resume tailoring based on master resume + JD
    - .docx and PDF export
    - 1-page constraint
    - ATS-friendly formatting (no tables, simple layout)
    """
    
    def __init__(self):
        self.output_dir = "data/resumes"
        os.makedirs(self.output_dir, exist_ok=True)
        app_logger.info("Resume generator initialized")
    
    def load_master_resume(self, resume_path: str = None) -> Optional[Dict]:
        """
        Load master resume from markdown or JSON
        
        Args:
            resume_path: Path to master resume file
        
        Returns:
            dict: Parsed resume data
        """
        if not resume_path:
            # Try to find master resume in default locations
            possible_paths = [
                "Yuting Sun Master Resume.md",
                "data/master_resume.md",
                "master_resume.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    resume_path = path
                    break
        
        if not resume_path or not os.path.exists(resume_path):
            app_logger.error("Master resume not found!")
            return None
        
        try:
            with open(resume_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse markdown resume (simple parser)
            resume_data = self._parse_markdown_resume(content)
            app_logger.info(f"Loaded master resume from {resume_path}")
            return resume_data
        
        except Exception as e:
            app_logger.error(f"Failed to load master resume: {e}")
            return None
    
    def _parse_markdown_resume(self, content: str) -> Dict:
        """Parse markdown resume into structured data"""
        lines = content.split('\n')
        
        resume = {
            "name": "",
            "contact": {},
            "summary": "",
            "experience": [],
            "education": [],
            "skills": [],
            "certifications": []
        }
        
        current_section = None
        current_item = None
        
        for line in lines:
            line = line.strip()
            
            # Extract name (usually first # header)
            if line.startswith('# ') and not resume["name"]:
                resume["name"] = line[2:].strip()
            
            # Section headers
            elif line.lower().startswith('## '):
                section_name = line[3:].lower().strip()
                if 'experience' in section_name or 'work' in section_name:
                    current_section = 'experience'
                elif 'education' in section_name:
                    current_section = 'education'
                elif 'skill' in section_name:
                    current_section = 'skills'
                elif 'summary' in section_name or 'profile' in section_name:
                    current_section = 'summary'
                elif 'certification' in section_name:
                    current_section = 'certifications'
            
            # Experience/Education items
            elif line.startswith('### '):
                if current_section in ['experience', 'education']:
                    if current_item:
                        resume[current_section].append(current_item)
                    current_item = {
                        "title": line[4:].strip(),
                        "details": []
                    }
            
            # Bullet points
            elif line.startswith('- ') or line.startswith('* '):
                if current_section == 'skills':
                    resume['skills'].append(line[2:].strip())
                elif current_item:
                    current_item['details'].append(line[2:].strip())
            
            # Summary text
            elif current_section == 'summary' and line:
                resume['summary'] += line + ' '
        
        # Add last item
        if current_item and current_section in ['experience', 'education']:
            resume[current_section].append(current_item)
        
        return resume
    
    def tailor_resume(self, master_resume: Dict, job_description: str, job_title: str, company: str) -> Dict:
        """
        Use AI to tailor resume for specific job
        
        Args:
            master_resume: Base resume data
            job_description: Target job JD
            job_title: Job title
            company: Company name
        
        Returns:
            dict: Tailored resume data
        """
        app_logger.info(f"Tailoring resume for {job_title} at {company}")
        
        # Build AI prompt
        prompt = f"""You are an expert resume writer specializing in ATS optimization.

**Task**: Tailor this resume for the following job, ensuring it passes ATS and appeals to HR.

**Job Details**:
- Title: {job_title}
- Company: {company}
- Job Description:
{job_description[:1500]}

**Master Resume**:
{json.dumps(master_resume, indent=2)}

**Requirements**:
1. Extract key skills/keywords from JD
2. Reorder/emphasize relevant experience
3. Add job-specific keywords naturally
4. Keep 1-page length (max 600 words)
5. Maintain truthfulness (don't fabricate)
6. Use action verbs and quantifiable achievements
7. Return JSON format matching master resume structure

**Output JSON** (experience items should include company, role, duration, bullets):
"""
        
        try:
            # Call GPT-4o-mini
            response = ai_agent.client.chat.completions.create(
                model=ai_agent.model,
                messages=[
                    {"role": "system", "content": "You are an expert ATS-optimized resume writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            
            # Extract JSON from response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()
            
            tailored_resume = json.loads(result)
            app_logger.info("Resume tailored successfully")
            
            return tailored_resume
        
        except Exception as e:
            app_logger.error(f"Resume tailoring failed: {e}")
            # Fallback: return master resume
            return master_resume
    
    def export_docx(self, resume_data: Dict, filename: str) -> str:
        """
        Export resume to .docx format (ATS-friendly)
        
        Args:
            resume_data: Resume data dict
            filename: Output filename
        
        Returns:
            str: Path to generated file
        """
        doc = Document()
        
        # Set narrow margins (ATS prefers simple layout)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.7)
            section.right_margin = Inches(0.7)
        
        # Name (centered, bold, larger)
        name = doc.add_paragraph(resume_data.get('name', 'Your Name'))
        name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        name.runs[0].bold = True
        name.runs[0].font.size = Pt(16)
        
        # Contact info (centered, smaller)
        contact = resume_data.get('contact', {})
        contact_text = ' | '.join([
            contact.get('email', ''),
            contact.get('phone', ''),
            contact.get('location', ''),
            contact.get('linkedin', '')
        ])
        contact_para = doc.add_paragraph(contact_text)
        contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_para.runs[0].font.size = Pt(10)
        
        doc.add_paragraph()  # Spacer
        
        # Summary
        if resume_data.get('summary'):
            summary_heading = doc.add_paragraph('PROFESSIONAL SUMMARY')
            summary_heading.runs[0].bold = True
            summary_heading.runs[0].font.size = Pt(11)
            
            summary_text = doc.add_paragraph(resume_data['summary'])
            summary_text.runs[0].font.size = Pt(10)
            doc.add_paragraph()
        
        # Experience
        if resume_data.get('experience'):
            exp_heading = doc.add_paragraph('PROFESSIONAL EXPERIENCE')
            exp_heading.runs[0].bold = True
            exp_heading.runs[0].font.size = Pt(11)
            
            for exp in resume_data['experience']:
                # Job title + company
                job_line = doc.add_paragraph()
                job_line.add_run(exp.get('title', '')).bold = True
                
                if exp.get('company'):
                    job_line.add_run(f" | {exp['company']}")
                
                if exp.get('duration'):
                    job_line.add_run(f" | {exp['duration']}")
                
                job_line.runs[0].font.size = Pt(10)
                
                # Bullets
                for detail in exp.get('details', []):
                    bullet = doc.add_paragraph(detail, style='List Bullet')
                    bullet.runs[0].font.size = Pt(10)
                
                doc.add_paragraph()  # Spacer between jobs
        
        # Education
        if resume_data.get('education'):
            edu_heading = doc.add_paragraph('EDUCATION')
            edu_heading.runs[0].bold = True
            edu_heading.runs[0].font.size = Pt(11)
            
            for edu in resume_data['education']:
                edu_line = doc.add_paragraph(edu.get('title', ''))
                edu_line.runs[0].bold = True
                edu_line.runs[0].font.size = Pt(10)
                
                for detail in edu.get('details', []):
                    doc.add_paragraph(detail, style='List Bullet').runs[0].font.size = Pt(10)
        
        # Skills
        if resume_data.get('skills'):
            skills_heading = doc.add_paragraph('SKILLS')
            skills_heading.runs[0].bold = True
            skills_heading.runs[0].font.size = Pt(11)
            
            skills_text = ', '.join(resume_data['skills'])
            doc.add_paragraph(skills_text).runs[0].font.size = Pt(10)
        
        # Save
        filepath = os.path.join(self.output_dir, filename)
        doc.save(filepath)
        app_logger.info(f"Resume exported to {filepath}")
        
        return filepath
    
    def export_pdf(self, resume_data: Dict, filename: str) -> str:
        """
        Export resume to PDF format
        
        Args:
            resume_data: Resume data dict
            filename: Output filename
        
        Returns:
            str: Path to generated file
        """
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                                topMargin=0.5*inch, bottomMargin=0.5*inch,
                                leftMargin=0.7*inch, rightMargin=0.7*inch)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Name
        name_style = ParagraphStyle('Name', parent=styles['Title'],
                                     fontSize=16, alignment=1, spaceAfter=6)
        story.append(Paragraph(resume_data.get('name', 'Your Name'), name_style))
        
        # Contact
        contact = resume_data.get('contact', {})
        contact_text = ' | '.join([
            contact.get('email', ''),
            contact.get('phone', ''),
            contact.get('location', '')
        ])
        contact_style = ParagraphStyle('Contact', parent=styles['Normal'],
                                        fontSize=10, alignment=1, spaceAfter=12)
        story.append(Paragraph(contact_text, contact_style))
        
        # Summary
        if resume_data.get('summary'):
            story.append(Paragraph('<b>PROFESSIONAL SUMMARY</b>', styles['Heading2']))
            story.append(Paragraph(resume_data['summary'], styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Experience
        if resume_data.get('experience'):
            story.append(Paragraph('<b>PROFESSIONAL EXPERIENCE</b>', styles['Heading2']))
            for exp in resume_data['experience']:
                title_text = f"<b>{exp.get('title', '')}</b>"
                if exp.get('company'):
                    title_text += f" | {exp['company']}"
                if exp.get('duration'):
                    title_text += f" | {exp['duration']}"
                
                story.append(Paragraph(title_text, styles['Normal']))
                
                for detail in exp.get('details', []):
                    story.append(Paragraph(f"• {detail}", styles['Normal']))
                
                story.append(Spacer(1, 0.05*inch))
        
        # Build PDF
        doc.build(story)
        app_logger.info(f"PDF exported to {filepath}")
        
        return filepath

# Global instance
resume_generator = ResumeGenerator()

if __name__ == "__main__":
    # Test
    gen = ResumeGenerator()
    master = gen.load_master_resume()
    
    if master:
        print("Master resume loaded:")
        print(f"Name: {master.get('name')}")
        print(f"Experience items: {len(master.get('experience', []))}")
