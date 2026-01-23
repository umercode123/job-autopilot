"""
Import Connections Script
导入现有LinkedIn connections到Memory
"""
import os
import sys
import asyncio
import re
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from modules.logger_config import app_logger
from modules.coffee_chat_memory import CoffeeChatMemory


class ConnectionImporter:
    """
    从LinkedIn导入现有connections到Memory
    用于避免向已连接的人重复发送请求
    """
    
    def __init__(self):
        self.session = None
        self.memory = CoffeeChatMemory()
    
    async def import_connections(self, max_pages: int = 5):
        """
        导入现有connections
        
        Args:
            max_pages: 最大翻页数
        """
        print("📥 Import Existing Connections")
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
                
                # Navigate to connections page
                print("\n📍 Opening LinkedIn Connections...")
                await session.call_tool("navigate_page", arguments={
                    "url": "https://www.linkedin.com/mynetwork/invite-connect/connections/",
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
                
                # Import connections
                all_connections = []
                
                for page in range(max_pages):
                    print(f"\n📄 Page {page + 1}/{max_pages}...")
                    
                    snapshot = await self._get_snapshot()
                    connections = self._parse_connections(snapshot)
                    
                    if not connections:
                        print("   No more connections found")
                        break
                    
                    # Filter out already imported
                    new_connections = []
                    for conn in connections:
                        if not self.memory.has_contacted(conn.get('linkedin_url', '')):
                            new_connections.append(conn)
                    
                    print(f"   Found {len(connections)} connections, {len(new_connections)} new")
                    all_connections.extend(new_connections)
                    
                    # Scroll down for more
                    await session.call_tool("press_key", arguments={"key": "End"})
                    await asyncio.sleep(2)
                
                # Save to memory
                print(f"\n💾 Saving {len(all_connections)} connections to memory...")
                
                for conn in all_connections:
                    contact_id = conn.get('linkedin_url', conn.get('name', ''))
                    self.memory.save_contact(contact_id, {
                        **conn,
                        'status': 'connected',
                        'imported_at': datetime.now().isoformat()
                    })
                
                print(f"\n✅ Imported {len(all_connections)} connections!")
                print("=" * 60)
                
                print("\nBrowser will close in 10 seconds...")
                await asyncio.sleep(10)
    
    async def _get_snapshot(self) -> str:
        """Get page snapshot"""
        result = await self.session.call_tool("take_snapshot", arguments={})
        return result.content[0].text if result.content else ""
    
    def _parse_connections(self, snapshot: str) -> List[Dict]:
        """Parse connections from snapshot"""
        connections = []
        current = {}
        
        lines = snapshot.split('\n')
        
        for i, line in enumerate(lines):
            # Look for profile links
            if 'linkedin.com/in/' in line and 'link' in line:
                if current:
                    connections.append(current)
                
                url_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-]+)', line)
                name_match = re.search(r'link "([^"]+)"', line)
                
                if url_match:
                    current = {
                        'linkedin_url': f"https://www.linkedin.com/in/{url_match.group(1)}",
                        'name': name_match.group(1) if name_match else 'Unknown',
                        'connection_degree': '1st'  # Already connected
                    }
            
            # Look for title/company
            elif current and 'StaticText' in line:
                text_match = re.search(r'StaticText "([^"]+)"', line)
                if text_match:
                    text = text_match.group(1)
                    if not current.get('title') and len(text) > 3:
                        if ' at ' in text:
                            parts = text.split(' at ')
                            current['title'] = parts[0]
                            current['company'] = parts[1] if len(parts) > 1 else ''
                        else:
                            current['title'] = text
        
        if current:
            connections.append(current)
        
        return connections


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import LinkedIn Connections')
    parser.add_argument('--pages', '-p', type=int, default=5,
                       help='Maximum pages to scroll (default: 5)')
    args = parser.parse_args()
    
    print("\n")
    print("=" * 60)
    print("   LinkedIn Connection Importer")
    print("=" * 60)
    print("\n⚠️ This will import your existing LinkedIn connections")
    print("   to avoid sending duplicate connection requests.")
    
    print(f"\n🚀 Starting in 3 seconds... (Ctrl+C to cancel)")
    
    try:
        await asyncio.sleep(3)
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        return
    
    importer = ConnectionImporter()
    
    try:
        await importer.import_connections(max_pages=args.pages)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
