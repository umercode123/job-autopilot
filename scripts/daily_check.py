"""
Daily Check Script
每日状态检查：检查连接请求状态，更新Memory
"""
import os
import sys
import asyncio
import re
from datetime import datetime, date
from typing import Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from modules.logger_config import app_logger
from modules.coffee_chat_memory import CoffeeChatMemory
from modules.rate_limiter import RateLimiter


class DailyChecker:
    """
    每日状态检查
    1. 检查pending连接请求
    2. 更新已接受的连接
    3. 生成统计报告
    """
    
    def __init__(self):
        self.session = None
        self.memory = CoffeeChatMemory()
        self.rate_limiter = RateLimiter()
    
    async def run_daily_check(self):
        """
        运行每日检查
        """
        print("📊 Daily Status Check")
        print("=" * 60)
        print(f"Date: {date.today()}")
        print("=" * 60)
        
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
                
                # Check login
                snapshot = await self._get_snapshot()
                if "sign in" in snapshot.lower():
                    print("⚠️ NOT LOGGED IN - Please login first!")
                    await asyncio.sleep(60)
                    return
                
                print("   ✅ Logged in")
                
                # Step 2: Check sent invitations
                print("\n📬 Step 2: Checking sent invitations...")
                await session.call_tool("navigate_page", arguments={
                    "url": "https://www.linkedin.com/mynetwork/invitation-manager/sent/",
                    "type": "url"
                })
                
                await asyncio.sleep(3)
                
                snapshot = await self._get_snapshot()
                pending_invites = self._parse_pending_invites(snapshot)
                
                print(f"   Found {len(pending_invites)} pending invitations")
                
                # Step 3: Check accepted connections
                print("\n✅ Step 3: Checking accepted connections...")
                
                # Get contacts from memory that are pending
                pending_contacts = self.memory.get_pending_contacts()
                
                accepted_count = 0
                for contact_id in pending_contacts:
                    # If not in pending invites, it was accepted (or withdrawn)
                    if not self._is_in_pending(contact_id, pending_invites):
                        self.memory.update_contact_status(contact_id, 'accepted')
                        accepted_count += 1
                        print(f"   ✅ Connection accepted: {contact_id[:50]}...")
                
                print(f"\n   {accepted_count} new connections accepted!")
                
                # Step 4: Get overall stats
                print("\n📈 Step 4: Generating statistics...")
                stats = self._generate_stats()
                
                print("\n" + "=" * 60)
                print("📊 DAILY REPORT")
                print("=" * 60)
                print(f"   📤 Total Sent: {stats['total_sent']}")
                print(f"   ⏳ Pending: {stats['pending']}")
                print(f"   ✅ Accepted: {stats['accepted']}")
                print(f"   ❌ Declined/Withdrawn: {stats['declined']}")
                if stats['total_sent'] > 0:
                    acceptance_rate = (stats['accepted'] / stats['total_sent']) * 100
                    print(f"   📊 Acceptance Rate: {acceptance_rate:.1f}%")
                print("=" * 60)
                
                # Rate limit status
                remaining = self.rate_limiter.get_remaining()
                print(f"\n📋 Today's Quota: {remaining['connections']} connections remaining")
                
                # Save report
                self._save_daily_report(stats)
                
                print("\n✅ Daily check complete!")
                print("Browser will close in 10 seconds...")
                await asyncio.sleep(10)
    
    async def _get_snapshot(self) -> str:
        """Get page snapshot"""
        result = await self.session.call_tool("take_snapshot", arguments={})
        return result.content[0].text if result.content else ""
    
    def _parse_pending_invites(self, snapshot: str) -> List[Dict]:
        """
        Parse pending invitations from snapshot
        """
        invites = []
        
        lines = snapshot.split('\n')
        current = {}
        
        for line in lines:
            # Look for profile links
            if 'linkedin.com/in/' in line:
                url_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-]+)', line)
                name_match = re.search(r'"([^"]+)"', line)
                
                if url_match:
                    if current:
                        invites.append(current)
                    
                    current = {
                        'linkedin_url': f"https://www.linkedin.com/in/{url_match.group(1)}",
                        'name': name_match.group(1) if name_match else 'Unknown'
                    }
            
            # Look for "Pending" or time indicators
            if current and ('pending' in line.lower() or 'week' in line.lower() or 'day' in line.lower()):
                current['status'] = 'pending'
        
        if current:
            invites.append(current)
        
        return invites
    
    def _is_in_pending(self, contact_id: str, pending_invites: List[Dict]) -> bool:
        """Check if contact is in pending invites"""
        for invite in pending_invites:
            if contact_id in invite.get('linkedin_url', ''):
                return True
            if contact_id in invite.get('name', ''):
                return True
        return False
    
    def _generate_stats(self) -> Dict:
        """Generate statistics from memory"""
        try:
            all_contacts = self.memory.get_all_contacts()
            
            total = len(all_contacts)
            pending = sum(1 for c in all_contacts if c.get('status') == 'pending')
            accepted = sum(1 for c in all_contacts if c.get('status') == 'accepted')
            declined = sum(1 for c in all_contacts if c.get('status') in ['declined', 'withdrawn'])
            
            return {
                'total_sent': total,
                'pending': pending,
                'accepted': accepted,
                'declined': declined,
                'date': str(date.today())
            }
        except Exception as e:
            app_logger.error(f"Error generating stats: {e}")
            return {
                'total_sent': 0,
                'pending': 0,
                'accepted': 0,
                'declined': 0,
                'date': str(date.today())
            }
    
    def _save_daily_report(self, stats: Dict):
        """Save daily report to file"""
        import json
        from pathlib import Path
        
        reports_dir = Path('data/daily_reports')
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = reports_dir / f"{date.today()}.json"
        
        report = {
            **stats,
            'generated_at': datetime.now().isoformat(),
            'rate_limit_status': self.rate_limiter.get_status()
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved: {report_file}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Status Check')
    parser.add_argument('--skip-browser', action='store_true', 
                       help='Skip browser check, only show local stats')
    args = parser.parse_args()
    
    print("\n")
    print("=" * 60)
    print("   LinkedIn Daily Status Check")
    print("=" * 60)
    
    if args.skip_browser:
        print("\n📊 Local stats only (no browser):")
        memory = CoffeeChatMemory()
        rate_limiter = RateLimiter()
        
        print(f"\nRate Limit Status:")
        status = rate_limiter.get_status()
        print(f"   Date: {status['date']}")
        print(f"   Connections sent today: {status['connections_sent']}")
        print(f"   Notes sent today: {status['notes_sent']}")
        print(f"   Remaining: {status['remaining_connections']} connections, {status['remaining_notes']} notes")
        
        return
    
    print("\n⚠️ This will open Chrome to check LinkedIn status")
    print("   Make sure you're logged in to LinkedIn")
    print(f"\n🚀 Starting in 3 seconds... (Ctrl+C to cancel)")
    
    try:
        await asyncio.sleep(3)
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        return
    
    checker = DailyChecker()
    
    try:
        await checker.run_daily_check()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
