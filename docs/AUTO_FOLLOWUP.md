# Job Autopilot - Auto Follow-up Feature

## Overview
After sending the initial cold email, the system automatically tracks responses and sends follow-up emails if no reply is received.

## How It Works

### Timeline
```
Day 0: Initial cold email sent ✉️
  ↓
Day 1-5: System checks hourly for HR reply
  ↓
Day 5: No reply detected
  ↓
  → AI generates follow-up email draft 📝
  → Notification sent to user
  ↓
User reviews and sends follow-up
```

### Follow-up Strategy

**Initial Email (Stage 1)**:
- Brief introduction (< 150 words)
- Highlight 1 relevant project
- Ask if they'd like to see resume
- **No attachment**

**Follow-up Email (Stage 2)** - Generated after 5 days:
```
Subject: Re: [Job Title] - Quick Follow-up

Hi {HR Name},

I wanted to follow up on my message from last week about the {Job Title} position at {Company}.

I understand you're likely busy reviewing many applications. I remain very interested in this opportunity and would love to discuss how my experience with {specific skill/project} aligns with your needs.

I've attached my resume for your review. Would you have 15 minutes this week for a brief call?

Best regards,
Yuting Sun

Portfolio: https://syttt.my.canva.site/
LinkedIn: https://www.linkedin.com/in/yuting-sun-48bbb4211/
```

### Configuration

**.env Settings**:
```env
# Wait 5 days before follow-up
FOLLOWUP_DELAY_DAYS=5

# Maximum 1 follow-up per job (avoid spam)
MAX_FOLLOWUPS_PER_JOB=1

# Enable auto follow-up
AUTO_FOLLOWUP_ENABLED=true
```

### Database Tracking

**Application Stages**:
1. `initial_draft` - Cold email created in Gmail drafts
2. `initial_sent` - User sent the initial email
3. `replied` - HR replied (no follow-up needed)
4. `followup_ready` - AI generated follow-up draft
5. `followup_sent` - User sent follow-up
6. `interview` - Interview scheduled
7. `rejected` - Rejection received
8. `offer` - Offer received

### Automated Process

**Daily Task** (runs every 24 hours):
```python
from modules.auto_followup import auto_followup_service

# Check all applications sent 5+ days ago
followups = auto_followup_service.check_and_create_followups()

# For each application needing follow-up:
# 1. Generate AI follow-up email
# 2. Create Gmail draft
# 3. Notify user
# 4. Update application status to 'followup_ready'
```

### User Notifications

**Streamlit Dashboard Alert**:
```
🔔 3 applications ready for follow-up:
- Senior Instructional Designer @ EdTech Solutions (sent 5 days ago)
- AI PM @ TechCorp Canada (sent 6 days ago)
- L&D Specialist @ Global Training (sent 7 days ago)

[Review Follow-ups] button
```

### AI Follow-up Email Generation

**GPT-4o-mini Prompt**:
```
Generate a follow-up email for this job (Stage 2: WITH resume attachment).

Context: 
- Initial email sent 5 days ago
- No reply received yet
- Keep tone polite and non-pushy

Requirements:
- Reference the initial email ("following up on my message from last week")
- Show continued interest
- Attach resume (mention "attached")
- Suggest specific meeting times
- Length: <200 words

Job: {job_title} at {company}
Initial email date: {sent_date}
```

### Best Practices

✅ **Do**:
- Wait at least 5 business days
- Keep follow-up brief and polite
- Reference the initial email
- Provide new value (attach resume now)
- Suggest specific times to show seriousness

❌ **Don't**:
- Send more than 1 follow-up per job
- Sound desperate or pushy
- Copy-paste the initial email
- Follow up before 3 days
- Send on weekends

### Success Metrics

Based on cold email research:
- Initial email reply rate: 1-5%
- With 1 follow-up: 15-20%
- **Total improvement: 3-4x higher response rate**

### Example Workflow

1. **Monday**: Send initial cold email to 5 companies
2. **Monday-Friday (Week 1)**: System checks hourly for replies
3. **Saturday (Day 6)**: Auto follow-up system runs
   - Generates 3 follow-up drafts (2 companies replied, 3 didn't)
   - Creates Gmail drafts
   - Sends notification
4. **Monday (Week 2)**: User reviews and sends 3 follow-ups
5. **Result**: 1 more HR replies (20% follow-up success rate)

### Future Enhancements (V2)

- [ ] A/B testing different follow-up templates
- [ ] Smart timing (send follow-ups on Tuesday mornings)
- [ ] Personalized follow-up based on company news
- [ ] LinkedIn connection request after email follow-up
- [ ] Auto-reschedule if Gmail draft not sent

---

**Implementation Status**: ✅ Implemented in `modules/auto_followup.py`
