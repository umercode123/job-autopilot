"""
LinkedIn Automation - Debug Version
Tests search and saves snapshots for debugging
"""
import os
import sys
import asyncio
import re
from typing import List, Dict, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logger_config import app_logger


async def test_linkedin_search():
    """
    Test LinkedIn search and save snapshots
    """
    print("🔍 LinkedIn Search Debug Test")
    print("=" * 60)
    
    async with stdio_client(
        StdioServerParameters(
            command="npx.cmd",
            args=["-y", "chrome-devtools-mcp@latest"],
            env=None
        )
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n1. Navigating to LinkedIn...")
            await session.call_tool(
                "navigate_page",
                arguments={"url": "https://www.linkedin.com", "type": "url"}
            )
            
            await asyncio.sleep(5)
            
            print("\n2. Taking homepage snapshot...")
            result = await session.call_tool("take_snapshot", arguments={})
            homepage_snapshot = result.content[0].text if result.content else ""
            
            # Save snapshot
            with open("linkedin_homepage_snapshot.txt", "w", encoding="utf-8") as f:
                f.write(homepage_snapshot)
            
            print(f"   ✅ Saved to linkedin_homepage_snapshot.txt")
            print(f"   Length: {len(homepage_snapshot)} chars")
            print(f"\n   First 1000 chars:")
            print(homepage_snapshot[:1000])
            
            # Check if we need to login
            if "sign in" in homepage_snapshot.lower() or "join now" in homepage_snapshot.lower():
                print("\n⚠️ NOT LOGGED IN")
                print("   Please manually login to LinkedIn in the browser")
                print("   Then press Enter to continue...")
                input()
            
            # Try searching for Shopify
            print("\n3. Searching for 'shopify.com' companies...")
            search_url = "https://www.linkedin.com/search/results/companies/?keywords=shopify.com"
            
            await session.call_tool(
                "navigate_page",
                arguments={"url": search_url, "type": "url"}
            )
            
            await asyncio.sleep(4)
            
            print("\n4. Taking company search snapshot...")
            result = await session.call_tool("take_snapshot", arguments={})
            company_snapshot = result.content[0].text if result.content else ""
            
            with open("linkedin_company_search_snapshot.txt", "w", encoding="utf-8") as f:
                f.write(company_snapshot)
            
            print(f"   ✅ Saved to linkedin_company_search_snapshot.txt")
            print(f"   Length: {len(company_snapshot)} chars")
            
            # Extract company URL
            match = re.search(r'linkedin\.com/company/([a-zA-Z0-9\-]+)', company_snapshot)
            if match:
                company_url = f"https://www.linkedin.com/company/{match.group(1)}"
                print(f"\n   ✅ Found company: {company_url}")
            else:
                print("\n   ❌ No company URL found in snapshot")
                print("\n   First 1000 chars of company search:")
                print(company_snapshot[:1000])
            
            # Try people search
            print("\n5. Searching for people: 'shopify University of Western Ontario'...")
            people_url = "https://www.linkedin.com/search/results/people/?keywords=shopify%20university%20of%20western%20ontario"
            
            await session.call_tool(
                "navigate_page",
                arguments={"url": people_url, "type": "url"}
            )
            
            await asyncio.sleep(4)
            
            print("\n6. Taking people search snapshot...")
            result = await session.call_tool("take_snapshot", arguments={})
            people_snapshot = result.content[0].text if result.content else ""
            
            with open("linkedin_people_search_snapshot.txt", "w", encoding="utf-8") as f:
                f.write(people_snapshot)
            
            print(f"   ✅ Saved to linkedin_people_search_snapshot.txt")
            print(f"   Length: {len(people_snapshot)} chars")
            
            # Try to parse contacts
            print("\n7. Parsing contacts from snapshot...")
            contacts = []
            current = {}
            
            for line in people_snapshot.split('\n'):
                if 'linkedin.com/in/' in line and 'link' in line:
                    if current:
                        contacts.append(current)
                    
                    url_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9\-]+)', line)
                    name_match = re.search(r'link "(.*?)"', line)
                    
                    if url_match and name_match:
                        current = {
                            'name': name_match.group(1),
                            'linkedin_url': f"https://www.linkedin.com/in/{url_match.group(1)}"
                        }
                        print(f"   Found: {current['name']}")
                
                elif current and ('• 2nd' in line or '• 3rd' in line):
                    degree = '2nd' if '• 2nd' in line else '3rd'
                    current['connection_degree'] = degree
                    print(f"      Degree: {degree}")
            
            if current:
                contacts.append(current)
            
            print(f"\n   ✅ Parsed {len(contacts)} contacts")
            
            if contacts:
                print("\n   Contacts:")
                for i, c in enumerate(contacts[:5], 1):
                    print(f"   {i}. {c.get('name')}")
                    print(f"      Degree: {c.get('connection_degree', 'Unknown')}")
                    print(f"      URL: {c.get('linkedin_url')}")
            
            print("\n" + "=" * 60)
            print("Test complete!")
            print("Check the saved snapshot files for details.")
            print("\nBrowser will stay open. Press Ctrl+C to close.")
            
            # Keep browser open
            await asyncio.sleep(300)


if __name__ == "__main__":
    try:
        asyncio.run(test_linkedin_search())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
