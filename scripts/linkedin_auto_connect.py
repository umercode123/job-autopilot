"""
LinkedIn Alumni Search & Auto-Connect
End-to-end automation: Search alumni → Send connection requests
"""
import os
import sys
import asyncio
import re
import random
from typing import List, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logger_config import app_logger
from modules.coffee_chat_agents import ContactRankerAgent, ScamDetectionAgent, PersonalizationAgent
from modules.coffee_chat_memory import CoffeeChatMemory


class LinkedInAutoConnect:
    """
    Complete LinkedIn automation:
    1. Search for alumni at a company
    2. Extract contacts from results
    3. Automatically send connection requests
    """
    
    def __init__(self):
        self.session = None
        self.memory = CoffeeChatMemory()
        self.ranker = ContactRankerAgent()
        self.scam_detector = ScamDetectionAgent()
        self.personalizer = PersonalizationAgent()
        app_logger.info("AI Agents and Memory initialized")
    
    async def run_auto_connect(
        self,
        domain: str,
        school: str,
        limit: int = 5,
        send_note: bool = True
    ):
        """
        Complete automation workflow
        
        Args:
            domain: Company domain (e.g., "shopify.com")
            school: School name
            limit: Max connection requests to send
            send_note: Whether to add personalized notes
        """
        print("🚀 LinkedIn Auto-Connect Workflow")
        print("=" * 60)
        print(f"   Company: {domain}")
        print(f"   School: {school}")
        print(f"   Max connections: {limit}")
        print(f"   Personalized notes: {send_note}")
        print("=" * 60)
        
        async with stdio_client(
            StdioServerParameters(
                command="npx.cmd",
                args=["-y", "chrome-devtools-mcp@latest", "--user-data-dir=C:/temp/linkedin-automation-profile"],  # Separate profile
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
                
                # Check if logged in
                snapshot = await self._get_snapshot()
                if "sign in" in snapshot.lower() or "join now" in snapshot.lower():
                    print("\n⚠️ NOT LOGGED IN - Please login to LinkedIn first!")
                    print("   The browser will stay open for 60 seconds...")
                    await asyncio.sleep(60)
                    return
                
                print("   ✅ Logged in to LinkedIn")
                
                # Step 2: Search for people
                print(f"\n🔍 Step 2: Searching for '{school}' alumni at '{domain}'...")
                
                # Remove domain extension for search
                company_name = domain.replace('.com', '').replace('.ca', '').replace('.io', '')
                
                search_url = (
                    f'https://www.linkedin.com/search/results/people/'
                    f'?keywords={company_name}%20{school}'
                )
                
                print(f"   URL: {search_url}")
                
                await session.call_tool("navigate_page", arguments={
                    "url": search_url,
                    "type": "url"
                })
                
                await asyncio.sleep(4)
                
                # Step 3: Extract contacts
                print("\n📋 Step 3: Extracting contacts from search results...")
                snapshot = await self._get_snapshot()
                
                contacts = self._parse_contacts(snapshot, limit * 2)  # Get extra in case some fail
                
                if not contacts:
                    print("   ❌ No contacts found!")
                    print("\n💡 Suggestions:")
                    print("   - Check if you're on the search results page")
                    print("   - Try a different keyword")
                    print("   - Make sure contacts have 'Connect' buttons (not 'Follow')")
                    return
                
                print(f"   ✅ Found {len(contacts)} potential contacts")
                
                # Filter contacts that have Connect button
                connectable = [c for c in contacts if c.get('connect_button_uid')]
                
                print(f"   ✅ {len(connectable)} have Connect buttons (2nd degree)")
                
                if not connectable:
                    print("\n   ⚠️ No 2nd degree connections found (all might be 3rd degree)")
                    print("   Try searching with different keywords or company")
                    return
                
                # Step 3.1: Filter out already contacted (Memory deduplication)
                print(f"\n🧠 Step 3.1: Checking Memory for duplicates...")
                new_contacts = []
                for contact in connectable:
                    contact_id = contact.get('linkedin_url', contact.get('name', ''))
                    if not self.memory.has_contacted(contact_id):
                        new_contacts.append(contact)
                    else:
                        print(f"   ⏭️ Skipping {contact.get('name')} (already contacted)")
                
                print(f"   ✅ {len(new_contacts)} new contacts (not contacted before)")
                
                if not new_contacts:
                    print("\n   ℹ️ All contacts have been contacted before")
                    return
                
                # Step 3.2: Scam detection
                print(f"\n🛡️ Step 3.2: Running scam detection...")
                safe_contacts = []
                for contact in new_contacts:
                    result = self.scam_detector.analyze_profile(contact)
                    
                    if result['is_safe']:
                        safe_contacts.append(contact)
                    else:
                        print(f"   ⚠️ Skipping {contact.get('name')} (risk score: {result['risk_score']}, flags: {result['flags']})")
                
                print(f"   ✅ {len(safe_contacts)} contacts passed scam check")
                
                if not safe_contacts:
                    print("\n   ⚠️ All contacts flagged as potentially suspicious")
                    return
                
                # Step 3.3: Rank contacts by priority
                print(f"\n⭐ Step 3.3: Ranking contacts by priority...")
                ranked = self.ranker.rank_contacts(safe_contacts)
                
                # Limit to requested number
                ranked = ranked[:limit]
                
                # Show preview
                print(f"\n📞 Will send connection requests to:")
                for i, contact in enumerate(ranked, 1):
                    print(f"   {i}. {contact['name']}")
                    print(f"      Priority: {contact.get('priority_score', 0):.1f}/100")
                    print(f"      Degree: {contact.get('connection_degree', 'Unknown')}")
                    print(f"      Company: {contact.get('company', 'N/A')}")
                
                print(f"\n🚀 Starting to send {len(ranked)} connection requests...")
                await asyncio.sleep(2)  # Brief pause
                
                # Step 4: Send connection requests
                print(f"\n💌 Step 4: Sending connection requests...\n")
                
                sent_count = 0
                failed_count = 0
                
                for i, contact in enumerate(ranked, 1):
                    print(f"\n[{i}/{len(ranked)}] Processing: {contact['name']}")
                    print(f"   Priority Score: {contact.get('priority_score', 0):.1f}/100")
                    
                    try:
                        # Send connection request (no note)
                        success = await self._send_connection(contact, note=None)
                        
                        if success:
                            print(f"   ✅ Connection request sent!")
                            sent_count += 1
                            
                            # Save to Memory
                            contact_id = contact.get('linkedin_url', contact.get('name', ''))
                            self.memory.save_contact(contact_id, contact)
                            self.memory.save_message(
                                contact_id=contact_id,
                                message_text="Direct connection (no note)",
                                message_type='connection_request',
                                response_status='pending'
                            )
                        else:
                            print(f"   ❌ Failed to send")
                            failed_count += 1
                        
                        # Rate limiting (random delay between 10-20 seconds for speed)
                        if i < len(ranked):
                            delay = random.randint(10, 20)
                            print(f"   ⏳ Waiting {delay}s before next request...")
                            await asyncio.sleep(delay)
                        
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
                        failed_count += 1
                
                # Summary
                print("\n" + "=" * 60)
                print("📊 SUMMARY")
                print("=" * 60)
                print(f"   ✅ Successfully sent: {sent_count}")
                print(f"   ❌ Failed: {failed_count}")
                print(f"   📝 Total processed: {sent_count + failed_count}")
                print("=" * 60)
                
                print("\n💡 Next steps:")
                print("   - Check LinkedIn to verify connections")
                print("   - Wait 3-5 days for responses")
                print("   - Send coffee chat messages to those who accept")
                
                print("\nBrowser will stay open. Press Ctrl+C to close.")
                await asyncio.sleep(300)
    
    async def _send_connection(self, contact: Dict, note: str = None) -> bool:
        """
        Send connection request to a contact
        
        Args:
            contact: Contact dict with connect_button_uid
            note: Optional personalized message
            
        Returns:
            True if successful
        """
        try:
            # Click Connect button
            connect_uid = contact.get('connect_button_uid')
            if not connect_uid:
                app_logger.error("No connect button UID")
                return False
            
            print(f"   🖱️ Clicking Connect button...")
            await self.session.call_tool("click", arguments={"uid": connect_uid})
            
            await asyncio.sleep(2)
            
            # Check if modal appeared
            snapshot = await self._get_snapshot()
            
            # Check if "Add a note" option exists
            if note and ("add a note" in snapshot.lower() or "how do you know" in snapshot.lower()):
                print(f"   ✍️ Adding personalized note...")
                
                # Try to find and click "Add a note" button
                add_note_match = re.search(r'uid=(\d+_\d+).*?[Aa]dd a note', snapshot)
                
                if add_note_match:
                    add_note_uid = add_note_match.group(1)
                    await self.session.call_tool("click", arguments={"uid": add_note_uid})
                    await asyncio.sleep(1)
                    
                    # Get updated snapshot
                    snapshot = await self._get_snapshot()
                
                # Find textarea
                textarea_match = re.search(r'uid=(\d+_\d+)\s+textbox', snapshot)
                
                if textarea_match:
                    textarea_uid = textarea_match.group(1)
                    
                    # Truncate note if needed
                    if len(note) > 300:
                        note = note[:297] + "..."
                    
                    await self.session.call_tool("fill", arguments={
                        "uid": textarea_uid,
                        "value": note
                    })
                    
                    await asyncio.sleep(0.5)
            
            # Find and click Send button
            print(f"   📤 Clicking Send...")
            snapshot = await self._get_snapshot()
            
            send_match = re.search(r'uid=(\d+_\d+).*?button.*?[Ss]end', snapshot)
            
            if send_match:
                send_uid = send_match.group(1)
                await self.session.call_tool("click", arguments={"uid": send_uid})
                await asyncio.sleep(1)
                return True
            else:
                # Maybe it's a direct send (no modal)
                print(f"   ℹ️ No Send button found, might be direct connection")
                return True
                
        except Exception as e:
            app_logger.error(f"Failed to send connection: {e}")
            return False
    
    async def _get_snapshot(self) -> str:
        """Get current page snapshot"""
        result = await self.session.call_tool("take_snapshot", arguments={})
        return result.content[0].text if result.content else ""
    
    def _parse_contacts(self, snapshot: str, limit: int) -> List[Dict]:
        """
        Parse contacts from LinkedIn search results snapshot
        
        Args:
            snapshot: Page snapshot
            limit: Max contacts to extract
            
        Returns:
            List of contact dictionaries
        """
        contacts = []
        current = {}
        
        lines = snapshot.split('\n')
        
        for i, line in enumerate(lines):
            # Look for LinkedIn profile links
            if 'linkedin.com/in/' in line and 'link' in line:
                # Save previous contact
                if current:
                    contacts.append(current)
                
                # Extract URL and name
                url_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-]+)', line)
                name_match = re.search(r'link "(.*?)"', line)
                
                if url_match and name_match:
                    current = {
                        'name': name_match.group(1),
                        'linkedin_url': f"https://www.linkedin.com/in/{url_match.group(1)}"
                    }
            
            # Connection degree
            elif current and ('• 2nd' in line or '• 3rd' in line):
                if '• 2nd' in line:
                    current['connection_degree'] = '2nd'
                elif '• 3rd' in line:
                    current['connection_degree'] = '3rd'
            
            # Connect button (only for 2nd degree)
            elif current and 'Invite' in line and 'to connect' in line:
                uid_match = re.search(r'uid=(\d+_\d+)', line)
                if uid_match:
                    current['connect_button_uid'] = uid_match.group(1)
            
            # Company info
            elif current and 'Current:' in line and not current.get('company'):
                # Look ahead for company name
                for j in range(i, min(i+3, len(lines))):
                    if 'StaticText' in lines[j] and '@' not in lines[j]:
                        company_match = re.search(r'StaticText "(.*?)"', lines[j])
                        if company_match and company_match.group(1).strip():
                            current['company'] = company_match.group(1)
                            break
            
            # Stop if we have enough
            if len(contacts) >= limit:
                break
        
        # Add last contact
        if current and len(contacts) < limit:
            contacts.append(current)
        
        return contacts[:limit]


# Main demo
async def main():
    """
    Main automation demo
    """
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='LinkedIn Auto-Connect')
    parser.add_argument('--company', '-c', type=str, default='google.com', 
                       help='Company domain or name to search')
    parser.add_argument('--school', '-s', type=str, default='University of Western Ontario',
                       help='School name to search alumni from')
    parser.add_argument('--limit', '-l', type=int, default=5,
                       help='Maximum connections to send')
    args = parser.parse_args()
    
    print("\n")
    print("=" * 60)
    print("   LinkedIn Auto-Connect")
    print("=" * 60)
    print("\n⚠️ IMPORTANT:")
    print("   - This will open Chrome browser")
    print("   - You need to login to LinkedIn manually")
    print("   - The script will then automatically:")
    print("     1. Search for alumni")
    print("     2. Send connection requests")
    print("     3. Add personalized notes")
    print("\n💡 Rate Limiting:")
    print(f"   - Max {args.limit} connections in this run")
    print("   - 10-20 seconds delay between each")
    print("   - LinkedIn limits: ~20 connections/day")
    print("\n" + "=" * 60)
    
    # Configuration from arguments
    domain = args.company
    school = args.school
    limit = args.limit
    
    print(f"\n📋 Configuration:")
    print(f"   Company: {domain}")
    print(f"   School: {school}")
    print(f"   Max connections: {limit}")
    
    print(f"\n🚀 Starting in 3 seconds... (Ctrl+C to cancel)")
    try:
        await asyncio.sleep(3)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return
    
    # Run automation
    automation = LinkedInAutoConnect()
    
    try:
        await automation.run_auto_connect(
            domain=domain,
            school=school,
            limit=limit,
            send_note=False  # No notes - save quota
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
