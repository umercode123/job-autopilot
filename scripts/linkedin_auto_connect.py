"""
LinkedIn Alumni Search & Auto-Connect (v2)
End-to-end automation with safety checks and new workflow

Phase 0: Safety checks (login, weekend, verification)
Phase 1: New workflow (company first, then alumni from multiple schools)
"""
import os
import sys
import asyncio
import re
import random
from datetime import datetime
from typing import List, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logger_config import app_logger
from modules.coffee_chat_agents import ContactRankerAgent, ScamDetectionAgent, PersonalizationAgent
from modules.coffee_chat_memory import CoffeeChatMemory
from modules.rate_limiter import RateLimiter
from modules.checkpoint import Checkpoint

# Try to import new Phase 2+ modules
try:
    from modules.agent_manager import AgentManager
    from modules.data_validator import DataValidator
    from modules.hidden_job_detector import HiddenJobDetector
    FULL_PIPELINE_AVAILABLE = True
except Exception as e:
    app_logger.warning(f"Full pipeline not available: {e}")
    FULL_PIPELINE_AVAILABLE = False

# Try to import Gmail service (optional)
try:
    from modules.gmail_service import gmail_service
    GMAIL_AVAILABLE = True
except Exception:
    GMAIL_AVAILABLE = False


# ============================================
# Phase 0: Safety Functions
# ============================================

def is_weekend() -> bool:
    """检查是否是周末（不发送连接请求）"""
    return datetime.now().weekday() >= 5


def get_current_time_status() -> Dict:
    """获取当前时间状态"""
    now = datetime.now()
    hour = now.hour
    
    # LinkedIn活跃时间：工作日 8am-6pm
    is_active_hours = 8 <= hour <= 18
    is_weekday = now.weekday() < 5
    
    return {
        'is_weekend': not is_weekday,
        'is_active_hours': is_active_hours,
        'current_hour': hour,
        'day_of_week': now.strftime('%A'),
        'should_send': is_weekday and is_active_hours,
        'reason': (
            'Weekend - not sending' if not is_weekday else
            'Outside active hours (8am-6pm)' if not is_active_hours else
            'Good time to send'
        )
    }


async def check_login_status(snapshot: str) -> str:
    """
    检查LinkedIn登录状态
    
    Returns:
        'logged_in' | 'logged_out' | 'verification_required'
    """
    snapshot_lower = snapshot.lower()
    
    # 检查是否需要登录
    if "sign in" in snapshot_lower or "join now" in snapshot_lower or "log in" in snapshot_lower:
        return "logged_out"
    
    # 检查是否需要验证
    verification_keywords = [
        "verification", "verify", "captcha", "security check",
        "confirm your identity", "phone number", "enter code"
    ]
    if any(kw in snapshot_lower for kw in verification_keywords):
        # 发送邮件通知
        if GMAIL_AVAILABLE:
            try:
                gmail_service.send_verification_alert()
                app_logger.info("Verification alert email sent")
            except Exception as e:
                app_logger.error(f"Failed to send verification alert: {e}")
        return "verification_required"
    
    return "logged_in"


def send_email_notification(subject: str, body: str) -> bool:
    """发送邮件通知"""
    if not GMAIL_AVAILABLE:
        app_logger.warning("Gmail service not available")
        return False
    
    try:
        return gmail_service.send_notification(subject, body)
    except Exception as e:
        app_logger.error(f"Failed to send email: {e}")
        return False


# ============================================
# Main Automation Class (Phase 1 workflow)
# ============================================

class LinkedInAutoConnect:
    """
    Complete LinkedIn automation with new workflow:
    1. Navigate to company page
    2. Go to People tab
    3. Filter by school(s)
    4. Extract and connect with alumni
    """
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.memory = CoffeeChatMemory()
        self.ranker = ContactRankerAgent()
        self.scam_detector = ScamDetectionAgent()
        self.personalizer = PersonalizationAgent()
        self.rate_limiter = RateLimiter()
        self.checkpoint = Checkpoint()
        app_logger.info("LinkedInAutoConnect v2 initialized with safety features")
    
    async def run_auto_connect(
        self,
        company: str,
        schools: List[str],
        limit: int = 5,
        send_note: bool = True,
        skip_weekend_check: bool = False
    ):
        """
        Complete automation workflow with new company-first approach
        
        Args:
            company: Company name or domain
            schools: List of school names to search
            limit: Max connection requests to send (total)
            send_note: Whether to add personalized notes  
            skip_weekend_check: Skip weekend restriction (for testing)
        """
        print("🚀 LinkedIn Auto-Connect v2")
        print("=" * 60)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 0: Safety Checks
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("\n🛡️ Phase 0: Safety Checks")
        
        # Check 1: Weekend
        if not skip_weekend_check:
            time_status = get_current_time_status()
            print(f"   📅 Day: {time_status['day_of_week']}")
            print(f"   ⏰ Hour: {time_status['current_hour']}:00")
            
            if time_status['is_weekend']:
                print("   ⚠️ WEEKEND - Not sending connection requests")
                print("   💡 LinkedIn connections perform better on weekdays")
                return
            
            if not time_status['is_active_hours']:
                print("   ⚠️ Outside active hours (8am-6pm)")
                print("   💡 Consider running during business hours for better response rates")
                # Continue anyway, just a warning
        
        # Check 2: Rate Limits
        remaining = self.rate_limiter.get_remaining()
        print(f"   📊 Daily quota: {remaining['connections']} connections, {remaining['notes']} notes remaining")
        
        if not self.rate_limiter.can_send_connection():
            print("   ❌ DAILY LIMIT REACHED - No more connections today")
            print(f"   💡 Limit resets at midnight")
            return
        
        # Adjust limit based on remaining quota
        actual_limit = min(limit, remaining['connections'])
        if actual_limit < limit:
            print(f"   ⚠️ Adjusting limit from {limit} to {actual_limit} (quota remaining)")
        
        print("\n   ✅ Safety checks passed!")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Phase 1: Main Workflow
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("\n🔧 Phase 1: Starting Company-First Workflow")
        print(f"   Company: {company}")
        print(f"   Schools: {schools}")
        print(f"   Max connections: {actual_limit}")
        print(f"   With notes: {send_note}")
        print("=" * 60)
        
        # Save checkpoint
        self.checkpoint.set_current_search(company, str(schools))
        
        async with stdio_client(
            StdioServerParameters(
                command="npx.cmd",
                args=["-y", "chrome-devtools-mcp@latest", "--user-data-dir=C:/temp/linkedin-automation-profile"],
                env=None
            )
        ) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()
                
                # Step 1: Navigate to LinkedIn
                print("\n📍 Step 1: Opening LinkedIn...")
                await session.call_tool("navigate_page", arguments={
                    "url": "https://www.linkedin.com",
                    "type": "url"
                })
                
                await asyncio.sleep(3)
                
                # Check login status
                snapshot = await self._get_snapshot()
                login_status = await check_login_status(snapshot)
                
                if login_status == "logged_out":
                    print("\n⚠️ NOT LOGGED IN - Please login to LinkedIn first!")
                    print("   The browser will stay open for 60 seconds...")
                    await asyncio.sleep(60)
                    return
                
                if login_status == "verification_required":
                    print("\n⚠️ VERIFICATION REQUIRED")
                    print("   LinkedIn is asking for verification.")
                    print("   An email notification has been sent.")
                    print("   Please complete verification manually.")
                    await asyncio.sleep(60)
                    return
                
                print("   ✅ Logged in to LinkedIn")
                
                # Step 2: Search for company
                print(f"\n🏢 Step 2: Searching for company '{company}'...")
                
                # Clean company name (remove domain extensions)
                company_name = company.replace('.com', '').replace('.ca', '').replace('.io', '').replace('.org', '')
                
                company_result = await self._find_company_page(company_name)
                
                if not company_result['found']:
                    print(f"   ❌ Company not found: {company}")
                    print("   💡 Try a different company name")
                    print("\n   Falling back to keyword search...")
                    # Fallback to keyword search
                    return await self._fallback_keyword_search(company, schools, actual_limit, send_note)
                
                print(f"   ✅ Found company: {company_result.get('name', company)}")
                
                # Step 3: Go to People tab
                print("\n👥 Step 3: Navigating to People tab...")
                await self._go_to_people_tab()
                
                # Step 4: Search alumni from each school
                print("\n🎓 Step 4: Searching for alumni...")
                all_contacts = []
                
                for school in schools:
                    print(f"\n   Searching: {school}")
                    contacts = await self._search_school_alumni(school)
                    print(f"   Found: {len(contacts)} contacts")
                    all_contacts.extend(contacts)
                
                # Deduplicate by LinkedIn URL
                unique_contacts = self._deduplicate_contacts(all_contacts)
                print(f"\n   ✅ Total unique contacts: {len(unique_contacts)}")
                
                if not unique_contacts:
                    print("\\n   ❌ No contacts found!")
                    print("   💡 Suggestions:")
                    print("     - Check if the company has employees")
                    print("     - Try different school names")
                    return
                
                # Step 5: Filter and process contacts
                print("\n🔍 Step 5: Processing contacts...")
                processed = await self._process_contacts(unique_contacts, actual_limit, send_note)
                
                # Summary
                print("\n" + "=" * 60)
                print("📊 SUMMARY")
                print("=" * 60)
                print(f"   ✅ Connections sent: {processed['sent']}")
                print(f"   ❌ Failed: {processed['failed']}")
                print(f"   ⏭️ Skipped (already contacted): {processed['skipped']}")
                print(f"   🛡️ Filtered (scam detection): {processed['filtered']}")
                
                # Rate limit status
                remaining = self.rate_limiter.get_remaining()
                print(f"\n   📊 Daily quota remaining: {remaining['connections']} connections")
                print("=" * 60)
                
                print("\n💡 Next steps:")
                print("   - Check LinkedIn to verify connections")
                print("   - Wait 3-5 days for responses")
                print("   - Run daily_check.py to update statuses")
                
                print("\nBrowser will stay open. Press Ctrl+C to close.")
                await asyncio.sleep(300)
    
    async def _find_company_page(self, company_name: str) -> Dict:
        """
        Find LinkedIn company page
        
        If multiple pages exist (e.g., Google, Amazon), shows them and picks the first.
        User can also provide a direct company URL.
        
        Returns:
            Dict with 'found', 'url', 'name'
        """
        try:
            # Check if company_name is already a URL
            if 'linkedin.com/company/' in company_name:
                url_match = re.search(r'linkedin\.com/company/([a-zA-Z0-9\-]+)', company_name)
                if url_match:
                    company_url = f"https://www.linkedin.com/company/{url_match.group(1)}"
                    print(f"   📎 Using direct URL: {company_url}")
                    await self.session.call_tool("navigate_page", arguments={
                        "url": company_url,
                        "type": "url"
                    })
                    await asyncio.sleep(2)
                    return {
                        'found': True,
                        'url': company_url,
                        'name': url_match.group(1)
                    }
            
            # Search for company
            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
            await self.session.call_tool("navigate_page", arguments={
                "url": search_url,
                "type": "url"
            })
            
            await asyncio.sleep(3)
            
            snapshot = await self._get_snapshot()
            
            # Find ALL company links in search results
            company_matches = re.findall(
                r'linkedin\.com/company/([a-zA-Z0-9\-]+)',
                snapshot
            )
            
            # Remove duplicates while preserving order
            seen = set()
            unique_companies = []
            for c in company_matches:
                if c not in seen:
                    seen.add(c)
                    unique_companies.append(c)
            
            if not unique_companies:
                print(f"   ❌ No company pages found for '{company_name}'")
                return {'found': False}
            
            if len(unique_companies) > 1:
                print(f"\n   ℹ️ Found {len(unique_companies)} company pages for '{company_name}':")
                for i, c in enumerate(unique_companies[:5], 1):
                    print(f"      {i}. linkedin.com/company/{c}")
                print(f"   → Using first result: {unique_companies[0]}")
                print(f"   💡 Tip: To use a specific page, run with --company 'linkedin.com/company/{unique_companies[1]}'")
            
            company_id = unique_companies[0]
            company_url = f"https://www.linkedin.com/company/{company_id}"
            
            # Navigate to company page
            await self.session.call_tool("navigate_page", arguments={
                "url": company_url,
                "type": "url"
            })
            
            await asyncio.sleep(2)
            
            return {
                'found': True,
                'url': company_url,
                'name': company_id
            }
        
        except Exception as e:
            app_logger.error(f"Error finding company: {e}")
            return {'found': False}
    
    async def _go_to_people_tab(self):
        """Navigate to People tab on company page"""
        try:
            snapshot = await self._get_snapshot()
            
            # Find People tab
            people_match = re.search(r'uid=(\d+_\d+).*?[Pp]eople', snapshot)
            
            if people_match:
                await self.session.call_tool("click", arguments={"uid": people_match.group(1)})
                await asyncio.sleep(2)
            else:
                # Try navigating directly
                current_url = snapshot.split('\n')[0] if snapshot else ""
                if 'linkedin.com/company/' in current_url:
                    company_id = re.search(r'/company/([^/]+)', current_url)
                    if company_id:
                        people_url = f"https://www.linkedin.com/company/{company_id.group(1)}/people/"
                        await self.session.call_tool("navigate_page", arguments={
                            "url": people_url,
                            "type": "url"
                        })
                        await asyncio.sleep(2)
        
        except Exception as e:
            app_logger.error(f"Error navigating to People tab: {e}")
    
    async def _search_school_alumni(self, school_name: str) -> List[Dict]:
        """
        Search for alumni from a specific school on the People page
        
        Returns:
            List of contact dictionaries
        """
        contacts = []
        
        try:
            # Get current snapshot
            snapshot = await self._get_snapshot()
            
            # Find school filter input
            school_input_match = re.search(
                r'uid=(\d+_\d+).*?textbox.*?[Ss]chool|[Ee]ducation',
                snapshot
            )
            
            if school_input_match:
                # Fill school filter
                await self.session.call_tool("fill", arguments={
                    "uid": school_input_match.group(1),
                    "value": school_name
                })
                await asyncio.sleep(2)
                
                # Press Enter or click search
                await self.session.call_tool("press_key", arguments={"key": "Enter"})
                await asyncio.sleep(3)
            else:
                # Use URL-based search
                current_url = snapshot.split('\n')[0] if snapshot else ""
                if 'linkedin.com' in current_url:
                    # Try keyword search instead
                    search_url = f"https://www.linkedin.com/search/results/people/?keywords={school_name}"
                    await self.session.call_tool("navigate_page", arguments={
                        "url": search_url,
                        "type": "url"
                    })
                    await asyncio.sleep(3)
            
            # Extract contacts
            snapshot = await self._get_snapshot()
            contacts = self._parse_contacts(snapshot, limit=20)
            
            # Tag contacts with school
            for contact in contacts:
                contact['school'] = school_name
            
        except Exception as e:
            app_logger.error(f"Error searching for school alumni: {e}")
        
        return contacts
    
    async def _process_contacts(
        self,
        contacts: List[Dict],
        limit: int,
        send_note: bool
    ) -> Dict:
        """
        Process contacts: filter, rank, send connections
        
        Returns:
            Dict with 'sent', 'failed', 'skipped', 'filtered' counts
        """
        stats = {'sent': 0, 'failed': 0, 'skipped': 0, 'filtered': 0}
        
        # Filter already contacted
        new_contacts = []
        for contact in contacts:
            contact_id = contact.get('linkedin_url', contact.get('name', ''))
            if self.memory.has_contacted(contact_id):
                stats['skipped'] += 1
                print(f"   ⏭️ Skipping {contact.get('name')} (already contacted)")
            else:
                new_contacts.append(contact)
        
        print(f"   {len(new_contacts)} new contacts (not contacted before)")
        
        if not new_contacts:
            return stats
        
        # Scam detection
        safe_contacts = []
        for contact in new_contacts:
            result = self.scam_detector.analyze_profile(contact)
            if result['is_safe']:
                safe_contacts.append(contact)
            else:
                stats['filtered'] += 1
                print(f"   🛡️ Filtered {contact.get('name')} (risk: {result['risk_score']})")
        
        print(f"   {len(safe_contacts)} passed scam check")
        
        if not safe_contacts:
            return stats
        
        # Rank contacts
        ranked = self.ranker.rank_contacts(safe_contacts)
        
        # Limit
        ranked = ranked[:limit]
        
        # Save checkpoint
        self.checkpoint.set_pending_contacts(ranked)
        
        # Send connections - REAL-TIME approach
        # Instead of iterating through a pre-collected list, we process one at a time
        # by finding the first available Connect button on the current page
        print(f"\n💌 Sending up to {len(ranked)} connection requests...")
        print(f"   📋 Contacts to process: {[c['name'] for c in ranked]}\n")
        
        processed_contacts = set()  # Track processed contact names
        attempts = 0
        max_attempts = len(ranked) + 5  # Allow some extra attempts
        
        while stats['sent'] < limit and attempts < max_attempts:
            attempts += 1
            
            # Check rate limit
            if not self.rate_limiter.can_send_connection():
                print(f"   ⚠️ Daily limit reached, stopping")
                break
            
            # Get fresh page snapshot
            snapshot = await self._get_snapshot()
            
            # Find first Connect button on current page that we haven't processed yet
            current_contact = None
            for target_contact in ranked:
                target_name = target_contact.get('name', '')
                if target_name in processed_contacts:
                    continue
                
                # Check if this contact is on the current page with a Connect button
                if target_name.lower() in snapshot.lower():
                    # Find their Connect button
                    new_uid = self._find_connect_button_for_contact(snapshot, target_contact)
                    if new_uid:
                        target_contact['connect_button_uid'] = new_uid
                        current_contact = target_contact
                        print(f"\n[{stats['sent']+1}/{limit}] Found {target_name} on page (UID: {new_uid})")
                        break
            
            if not current_contact:
                print(f"   ⚠️ No more contacts found on current page with Connect buttons")
                break
            
            contact = current_contact
            processed_contacts.add(contact['name'])
            
            print(f"   Score: {contact.get('priority_score', 0):.1f}/100")
            
            try:
                # Generate note if enabled and quota available
                note = None
                if send_note and self.rate_limiter.can_send_note():
                    note = await self._generate_note(contact)
                    if note:
                        self.rate_limiter.record_note()
                
                # Send connection
                success = await self._send_connection(contact, note)
                
                if success:
                    print(f"   ✅ Connection sent!")
                    stats['sent'] += 1
                    self.rate_limiter.record_connection(contact.get('linkedin_url'))
                    
                    # Save to memory
                    contact_id = contact.get('linkedin_url', contact.get('name', ''))
                    self.memory.save_contact(contact_id, contact)
                    self.memory.save_message(
                        contact_id=contact_id,
                        message_text=note or "Direct connection (no note)",
                        message_type='connection_request',
                        response_status='pending'
                    )
                    
                    # Mark in checkpoint
                    self.checkpoint.mark_contact_processed(contact_id)
                else:
                    print(f"   ❌ Failed to send")
                    stats['failed'] += 1
                
                # Rate limiting delay (no page refresh - we'll scan the current page again)
                if stats['sent'] < limit:
                    delay = random.randint(10, 20)
                    print(f"   ⏳ Waiting {delay}s before next contact...")
                    await asyncio.sleep(delay)
            
            except Exception as e:
                print(f"   ❌ Error: {e}")
                stats['failed'] += 1
                processed_contacts.add(contact.get('name', ''))  # Skip this contact
        
        return stats
    
    def _find_connect_button_for_contact(self, snapshot: str, contact: Dict) -> Optional[str]:
        """Find Connect button UID for a specific contact in the snapshot"""
        contact_name = contact.get('name', '')
        if not contact_name:
            return None
        
        lines = snapshot.split('\n')
        found_contact_line = -1
        
        # First, find the line containing the contact's name
        for i, line in enumerate(lines):
            if contact_name.lower() in line.lower() and 'linkedin.com/in/' in line:
                found_contact_line = i
                print(f"   🔍 Found contact at line {i}: {line[:80]}...")
                break
        
        if found_contact_line == -1:
            print(f"   ⚠️ Contact '{contact_name}' not found in current page")
            return None
        
        # Now search for Connect button in the next 30 lines
        for j in range(found_contact_line, min(found_contact_line + 30, len(lines))):
            line = lines[j]
            line_lower = line.lower()
            
            # STRICT CHECK: Must be a button, not a link
            is_button = 'button ' in line_lower or ' role="button"' in line_lower or line_lower.strip().endswith('button')
            is_link = 'link ' in line_lower or ' role="link"' in line_lower
            
            if is_link and not is_button:
                continue  # Skip links
            
            # Pattern 1: "Invite [Name] to connect" button
            if 'invite' in line_lower and 'to connect' in line_lower:
                uid_match = re.search(r'uid=(\d+_\d+)', line)
                if uid_match:
                    print(f"   ✅ Found Connect button (Invite) at line {j} (UID: {uid_match.group(1)})")
                    return uid_match.group(1)
            
            # Pattern 2: "+ Connect" button
            if 'connect' in line_lower and 'message' not in line_lower:
                uid_match = re.search(r'uid=(\d+_\d+)', line)
                if uid_match:
                    # Make sure it's not a "Message" or "Pending" button
                    if 'pending' not in line_lower:
                        print(f"   ✅ Found Connect button at line {j} (UID: {uid_match.group(1)})")
                        return uid_match.group(1)
        
        print(f"   ⚠️ No Connect button found for '{contact_name}' in next 30 lines")
        return None
    
    async def _generate_note(self, contact: Dict) -> Optional[str]:
        """Generate personalized connection note"""
        try:
            note = self.personalizer.generate_message({
                'name': contact.get('name', 'there'),
                'company': contact.get('company', ''),
                'title': contact.get('title', ''),
                'school': contact.get('school', '')
            })
            
            # Add AI disclosure
            if note and "(AI-assisted" not in note:
                note += "\n\n(AI-assisted via job-autopilot)"
            
            # Truncate if needed
            if note and len(note) > 300:
                note = note[:297] + "..."
            
            return note
        except Exception as e:
            app_logger.error(f"Error generating note: {e}")
            return None
    
    async def _send_connection(self, contact: Dict, note: str = None) -> bool:
        """Send connection request to a contact using JavaScript (handles Search & Profile pages)"""
        try:
            contact_name = contact.get('name', '')
            
            # 1. Determine which page we are on using DOM detection (more reliable than URL)
            page_type_obj = await self.session.call_tool("evaluate_script", arguments={
                "function": """() => {
                    if (document.querySelector('.pv-top-card, .pv-text-details__left-panel')) {
                        return 'profile';
                    }
                    if (document.querySelector('.reusable-search__result-container')) {
                        return 'search';
                    }
                    return 'unknown';
                }"""
            })
            page_type = page_type_obj.content[0].text if page_type_obj.content else "unknown"
            
            # Additional check: URL fallback
            if 'profile' not in page_type and 'search' not in page_type:
                url_obj = await self.session.call_tool("evaluate_script", arguments={"function": "() => window.location.href"})
                url = url_obj.content[0].text if url_obj.content else ""
                if "/in/" in url: page_type = 'profile'
                elif "search" in url: page_type = 'search'

            print(f"   📍 Detected Page Type: {page_type}")
            
            # DEBUG: Take screenshot
            await self._save_debug_screenshot(f"start_{contact_name}")
            
            js_click_success = False
            
            # === SCENARIO A: PROFILE PAGE ===
            if 'profile' in page_type:
                print(f"   👤 Processing Profile Page for '{contact_name}'")
                
                # JS to find Connect button on Profile Page
                js_click_result = await self.session.call_tool("evaluate_script", arguments={
                    "function": """() => {
                        // Helper to find visible buttons
                        const buttons = Array.from(document.querySelectorAll('button'));
                        
                        // 1. Try Primary Connect Button (explicit text)
                        const connectBtn = buttons.find(b => {
                            const text = b.textContent.trim().toLowerCase();
                            return (text === 'connect' || text === 'connect\n') && !b.disabled && b.offsetParent !== null;
                        });
                        
                        if (connectBtn) {
                            connectBtn.click();
                            return { success: true, method: 'primary_button_text' };
                        }
                        
                        // 2. Try by Aria Label
                        const ariaBtn = buttons.find(b => {
                            const label = (b.getAttribute('aria-label') || '').toLowerCase();
                            return label.includes('connect with') || label.includes('invite') && label.includes('connect');
                        });
                        if (ariaBtn && ariaBtn.offsetParent !== null) {
                            ariaBtn.click();
                            return { success: true, method: 'aria_label' };
                        }
                        
                        // 3. Try "More" menu -> "Connect"
                        // This implies opening the menu first.
                        const moreBtn = buttons.find(b => 
                            (b.getAttribute('aria-label') || '').toLowerCase().includes('more actions')
                        );
                        
                        if (moreBtn) {
                            moreBtn.click();
                            // We can't click the dropdown item immediately in the same tick usually, 
                            // but let's try to return instruction to click content
                            return { success: false, reason: 'Clicked More menu, waiting for dropdown' };
                        }
                        
                        return { success: false, reason: 'Connect button not found directly' };
                    }"""
                })
                
                if js_click_result and hasattr(js_click_result, 'content') and '"success":true' in str(js_click_result.content):
                    js_click_success = True
                    print(f"   ✅ Clicked Connect on Profile Page!")
                elif hasattr(js_click_result, 'content') and 'Clicked More menu' in str(js_click_result.content):
                    print(f"   🖱️ Clicked 'More' menu, looking for Connect option...")
                    await asyncio.sleep(1)
                    # Try to click Connect in the dropdown
                    await self.session.call_tool("evaluate_script", arguments={
                        "function": """() => {
                            const items = Array.from(document.querySelectorAll('div[role="button"], span'));
                            const connectItem = items.find(i => i.textContent.trim().toLowerCase() === 'connect');
                            if (connectItem) {
                                connectItem.click();
                                return { success: true };
                            }
                            return { success: false };
                        }"""
                    })
                    js_click_success = True # Assume success to trigger modal check
            
            # === SCENARIO B: SEARCH RESULTS PAGE ===
            else:
                print(f"   🔍 Processing Search Page for '{contact_name}'")
                
                js_click_result = await self.session.call_tool("evaluate_script", arguments={
                    "function": f"""() => {{
                        const targetName = "{contact_name.lower()}";
                        // Find result cards
                        const cards = document.querySelectorAll('.entity-result, .reusable-search__result-container');
                        
                        for (const card of cards) {{
                            // Check name
                            if (!card.textContent.toLowerCase().includes(targetName)) continue;
                            
                            // Find Connect Button STRICTLY
                            // Look for <button> with "Connect" text, exclude "Message"
                            const buttons = card.querySelectorAll('button');
                            for (const btn of buttons) {{
                                const text = btn.innerText.toLowerCase().trim();
                                if (text === 'connect' || text === 'invite') {{
                                    // Verify it's not hidden
                                    if (btn.offsetParent !== null) {{
                                        btn.click();
                                        return {{ success: true, name: targetName }};
                                    }}
                                }}
                                // Try aria-label for "Invite [Name] to connect"
                                const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                                if (label.includes('invite') && label.includes('connect') && label.includes(targetName)) {{
                                     btn.click();
                                     return {{ success: true, method: 'aria-label' }};
                                }}
                            }}
                        }}
                        return {{ success: false, reason: 'Cards scanned, button not found' }};
                    }}"""
                })
                
                if js_click_result and hasattr(js_click_result, 'content') and '"success":true' in str(js_click_result.content):
                    js_click_success = True
                    print(f"   ✅ Clicked Connect on Search Page!")

            # === FALLBACK LOGIC ===
            if not js_click_success:
                print(f"   ⚠️ JS click failed, falling back to UID click...")
                
                # Check if we have a valid UID from the snapshot analysis
                connect_uid = contact.get('connect_button_uid')
                if connect_uid:
                    print(f"   🔄 Fallback: Clicking UID {connect_uid}...")
                    await self.session.call_tool("click", arguments={"uid": connect_uid})
                    # Give it a moment to react
                    await asyncio.sleep(2)
                else:
                    print(f"   ❌ No fallback UID available")
                    return False

            # Wait for modal

            print(f"   ⏳ Waiting for modal...")
            await asyncio.sleep(3)
            await self._save_debug_screenshot(f"modal_check_{contact_name}")
            
            # Handle Modal
            print(f"   📤 Clicking 'Send without a note'...")
            
            # 1. Try JavaScript Click
            js_send_result = await self.session.call_tool("evaluate_script", arguments={
                "function": """() => {
                    const modal = document.querySelector('[role="dialog"]');
                    if (!modal) return { success: false, reason: 'No modal' };
                    
                    const buttons = Array.from(modal.querySelectorAll('button'));
                    // Priority 1: "Send without a note"
                    const sendNoNote = buttons.find(b => b.innerText.toLowerCase().includes('send without'));
                    if (sendNoNote) { sendNoNote.click(); return { success: true, method: 'js_text' }; }
                    
                    // Priority 2: Aria Label
                    const ariaSend = buttons.find(b => (b.getAttribute('aria-label')||'').toLowerCase().includes('send without'));
                    if (ariaSend) { ariaSend.click(); return { success: true, method: 'js_aria' }; }

                    // Priority 3: "Send"
                    const send = buttons.find(b => b.innerText.toLowerCase().trim() === 'send');
                    if (send) { send.click(); return { success: true, method: 'js_send_text' }; }
                    
                    return { success: false, reason: 'No send button' };
                }"""
            })
            
            await asyncio.sleep(1)
            
            # 2. Check if modal is gone. If not, try UID Click (Fallback)
            snapshot = await self._get_snapshot()
            if "add a note" in snapshot.lower():
                print(f"   ⚠️ Modal still present after JS click, trying UID fallback...")
                
                # Find the button UID in the snapshot
                send_uid = None
                lines = snapshot.split('\n')
                for line in lines:
                    line_lower = line.lower()
                    if 'send without a note' in line_lower and 'button' in line_lower:
                        uid_match = re.search(r'uid=(\d+_\d+)', line)
                        if uid_match:
                            send_uid = uid_match.group(1)
                            print(f"   ✅ Found 'Send without a note' button (UID: {send_uid})")
                            break
                    if not send_uid and 'send' in line_lower and 'button' in line_lower and 'note' not in line_lower:
                         # Fallback for just "Send"
                         uid_match = re.search(r'uid=(\d+_\d+)', line)
                         if uid_match:
                            send_uid = uid_match.group(1)
                
                if send_uid:
                    print(f"   🖱️ Clicking Send button UID: {send_uid}...")
                    await self.session.call_tool("click", arguments={"uid": send_uid})
                    await asyncio.sleep(2)
            
            # 3. Final Fallback: Enter key
            snapshot = await self._get_snapshot()
            if "add a note" in snapshot.lower():
                print(f"   📤 Fallback: Pressing Enter...")
                await self.session.call_tool("press_key", arguments={"key": "Enter"})
                await asyncio.sleep(1)
            
            # Final verification
            snapshot = await self._get_snapshot()
            if "add a note" not in snapshot.lower():
                print(f"   ✅ Modal closed (verified)")
                return True
                
            return False
        
        except Exception as e:
            app_logger.error(f"Failed to send connection: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _fallback_keyword_search(
        self,
        company: str,
        schools: List[str],
        limit: int,
        send_note: bool
    ):
        """Fallback to keyword-based search if company page not found"""
        print("\n🔄 Using keyword search fallback...")
        
        all_contacts = []
        
        for school in schools:
            # Clean names
            company_name = company.replace('.com', '').replace('.ca', '').replace('.io', '')
            
            search_url = (
                f'https://www.linkedin.com/search/results/people/'
                f'?keywords={company_name}%20{school}'
            )
            
            print(f"   Searching: {company_name} + {school}")
            
            await self.session.call_tool("navigate_page", arguments={
                "url": search_url,
                "type": "url"
            })
            
            await asyncio.sleep(4)
            
            snapshot = await self._get_snapshot()
            contacts = self._parse_contacts(snapshot, limit=20)
            
            for contact in contacts:
                contact['school'] = school
            
            all_contacts.extend(contacts)
            print(f"   Found: {len(contacts)} contacts")
        
        # Deduplicate
        unique = self._deduplicate_contacts(all_contacts)
        print(f"\n   ✅ Total unique: {len(unique)} contacts")
        
        if unique:
            await self._process_contacts(unique, limit, send_note)
    
    async def _save_debug_screenshot(self, name: str):
        """Save debug screenshot to data/debug_screenshots/"""
        try:
            import os
            from pathlib import Path
            
            # Create debug directory
            debug_dir = Path("data/debug_screenshots")
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Clean name for filename
            clean_name = re.sub(r'[^\w\-]', '_', name)
            filepath = debug_dir / f"{timestamp}_{clean_name}.png"
            
            # Take screenshot using MCP tool
            await self.session.call_tool("take_screenshot", arguments={
                "filePath": str(filepath.absolute())
            })
            
            print(f"   📸 Screenshot saved: {filepath}")
        except Exception as e:
            print(f"   ⚠️ Screenshot failed: {e}")
    
    async def _get_snapshot(self) -> str:
        """Get current page snapshot"""
        result = await self.session.call_tool("take_snapshot", arguments={})
        return result.content[0].text if result.content else ""
    
    def _parse_contacts(self, snapshot: str, limit: int) -> List[Dict]:
        """Parse contacts from LinkedIn search results snapshot"""
        contacts = []
        current = {}
        
        lines = snapshot.split('\n')
        
        for i, line in enumerate(lines):
            # LinkedIn profile links
            if 'linkedin.com/in/' in line and 'link' in line:
                if current:
                    contacts.append(current)
                
                url_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-]+)', line)
                name_match = re.search(r'link "([^"]*)"', line)
                
                if url_match and name_match:
                    current = {
                        'name': name_match.group(1),
                        'linkedin_url': f"https://www.linkedin.com/in/{url_match.group(1)}"
                    }
            
            # Connection degree
            elif current and ('• 2nd' in line or '• 3rd' in line):
                current['connection_degree'] = '2nd' if '• 2nd' in line else '3rd'
            
            # Connect button
            elif current and 'Invite' in line and 'to connect' in line:
                uid_match = re.search(r'uid=(\d+_\d+)', line)
                if uid_match:
                    current['connect_button_uid'] = uid_match.group(1)
            
            # Company info
            elif current and 'Current:' in line and not current.get('company'):
                for j in range(i, min(i+3, len(lines))):
                    if 'StaticText' in lines[j] and '@' not in lines[j]:
                        company_match = re.search(r'StaticText "([^"]*)"', lines[j])
                        if company_match and company_match.group(1).strip():
                            current['company'] = company_match.group(1)
                            break
            
            if len(contacts) >= limit:
                break
        
        if current and len(contacts) < limit:
            contacts.append(current)
        
        # Only return contacts with Connect button (2nd degree)
        return [c for c in contacts if c.get('connect_button_uid')][:limit]
    
    def _deduplicate_contacts(self, contacts: List[Dict]) -> List[Dict]:
        """Remove duplicate contacts by LinkedIn URL"""
        seen = set()
        unique = []
        
        for contact in contacts:
            url = contact.get('linkedin_url', '')
            if url and url not in seen:
                seen.add(url)
                unique.append(contact)
        
        return unique


# ============================================
# Main Entry Point
# ============================================

async def main():
    """Main automation entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Auto-Connect v2')
    parser.add_argument('--company', '-c', type=str, default='google.com',
                       help='Company name or domain')
    parser.add_argument('--school', '-s', type=str, nargs='+',
                       default=['University of Western Ontario'],
                       help='School name(s) to search')
    parser.add_argument('--limit', '-l', type=int, default=5,
                       help='Max connections to send')
    parser.add_argument('--no-note', action='store_true',
                       help='Do not include personalized notes')
    parser.add_argument('--skip-weekend', action='store_true',
                       help='Skip weekend check (for testing)')
    args = parser.parse_args()
    
    print("\n")
    print("=" * 60)
    print("   LinkedIn Auto-Connect v2")
    print("   with Safety Checks & Company-First Workflow")
    print("=" * 60)
    
    print("\n⚠️ IMPORTANT:")
    print("   - This will open Chrome browser")
    print("   - Login to LinkedIn if needed")
    print("   - New workflow: Company → People → School Filter")
    
    print("\n🛡️ Safety Features:")
    print("   - Weekend detection (no send on weekends)")
    print("   - Daily rate limiting (20 connections/day)")
    print("   - Verification detection with email alerts")
    print("   - Scam detection and filtering")
    
    print("\n📋 Configuration:")
    print(f"   Company: {args.company}")
    print(f"   Schools: {args.school}")
    print(f"   Max connections: {args.limit}")
    print(f"   With notes: {not args.no_note}")
    
    print(f"\n🚀 Starting in 3 seconds... (Ctrl+C to cancel)")
    try:
        await asyncio.sleep(3)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return
    
    automation = LinkedInAutoConnect()
    
    try:
        await automation.run_auto_connect(
            company=args.company,
            schools=args.school if isinstance(args.school, list) else [args.school],
            limit=args.limit,
            send_note=not args.no_note,
            skip_weekend_check=args.skip_weekend
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
