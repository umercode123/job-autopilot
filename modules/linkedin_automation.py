"""
LinkedIn Automation - Async Version
Uses Chrome DevTools MCP for browser automation
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


class LinkedInAutomation:
    """Automated LinkedIn search using Chrome DevTools MCP"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
    
    async def search_alumni_by_domain(
        self, 
        domain: str, 
        school_name: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search for alumni at a company using domain
        
        Args:
            domain: Company domain (e.g., "shopify.com")
            school_name: School name
            limit: Max results
            
        Returns:
            List of contact dictionaries
        """
        contacts = []
        
        async with stdio_client(
            StdioServerParameters(
                command="npx.cmd",
                args=["-y", "chrome-devtools-mcp@latest"],
                env=None
            )
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                try:
                    # Step 1: Try to find company page
                    app_logger.info(f"Searching for company: {domain}")
                    company_url = await self._find_company_page(session, domain)
                    
                    if company_url:
                        # Step 2a: Search using company filter
                        app_logger.info(f"Found company page: {company_url}")
                        contacts = await self._search_by_company(
                            session, company_url, school_name, limit
                        )
                    else:
                        # Step 2b: Keyword search
                        app_logger.warning(f"No company page, using keyword search")
                        contacts = await self._search_by_keyword(
                            session, domain, school_name, limit
                        )
                    
                    return contacts
                    
                except Exception as e:
                    app_logger.error(f"Search failed: {e}")
                    return []
    
    async def _find_company_page(
        self, 
        session: ClientSession, 
        domain: str
    ) -> Optional[str]:
        """Find LinkedIn company page by domain"""
        try:
            # Navigate to company search
            search_url = f"https://www.linkedin.com/search/results/companies/?keywords={domain}"
            
            await session.call_tool(
                "navigate_page",
                arguments={"url": search_url, "type": "url"}
            )
            
            await asyncio.sleep(3)  # Wait for results
            
            # Get snapshot
            result = await session.call_tool("take_snapshot", arguments={})
            snapshot = result.content[0].text if result.content else ""
            
            # Extract company URL
            match = re.search(r'linkedin\.com/company/([a-zA-Z0-9\-]+)', snapshot)
            if match:
                return f"https://www.linkedin.com/company/{match.group(1)}"
            
            return None
            
        except Exception as e:
            app_logger.error(f"Failed to find company: {e}")
            return None
    
    async def _search_by_company(
        self,
        session: ClientSession,
        company_url: str,
        school_name: str,
        limit: int
    ) -> List[Dict]:
        """Search using company page filter"""
        try:
            company_id = company_url.split('/')[-1]
            
            # Build search URL with filters
            search_url = (
                f'https://www.linkedin.com/search/results/people/'
                f'?currentCompany=%5B"{company_id}"%5D'
                f'&keywords={school_name}'
            )
            
            await session.call_tool(
                "navigate_page",
                arguments={"url": search_url, "type": "url"}
            )
            
            await asyncio.sleep(4)
            
            # Get snapshot
            result = await session.call_tool("take_snapshot", arguments={})
            snapshot = result.content[0].text if result.content else ""
            
            # Extract contacts
            contacts = self._parse_contacts(snapshot, limit)
            
            for contact in contacts:
                contact['search_method'] = 'company_page'
                contact['domain_verified'] = True
            
            return contacts
            
        except Exception as e:
            app_logger.error(f"Company search failed: {e}")
            return []
    
    async def _search_by_keyword(
        self,
        session: ClientSession,
        domain: str,
        school_name: str,
        limit: int
    ) -> List[Dict]:
        """Search using keywords (fallback)"""
        try:
            # Remove domain extensions
            company_base = domain.replace('.com', '').replace('.ca', '').replace('.io', '')
            
            search_url = (
                f'https://www.linkedin.com/search/results/people/'
                f'?keywords={company_base}%20{school_name}'
            )
            
            await session.call_tool(
                "navigate_page",
                arguments={"url": search_url, "type": "url"}
            )
            
            await asyncio.sleep(4)
            
            # Get snapshot
            result = await session.call_tool("take_snapshot", arguments={})
            snapshot = result.content[0].text if result.content else ""
            
            # Extract and verify
            all_contacts = self._parse_contacts(snapshot, limit * 2)
            
            verified = []
            for contact in all_contacts:
                if company_base.lower() in contact.get('company', '').lower():
                    contact['search_method'] = 'keyword'
                    contact['domain_verified'] = True
                    verified.append(contact)
                    if len(verified) >= limit:
                        break
            
            return verified
            
        except Exception as e:
            app_logger.error(f"Keyword search failed: {e}")
            return []
    
    def _parse_contacts(self, snapshot: str, limit: int) -> List[Dict]:
        """Parse contacts from LinkedIn search snapshot"""
        contacts = []
        current = {}
        
        for line in snapshot.split('\n'):
            # LinkedIn profile URL
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
            
            # Connection degree
            elif current and ('• 2nd' in line or '• 3rd' in line):
                if '• 2nd' in line:
                    current['connection_degree'] = '2nd'
                else:
                    current['connection_degree'] = '3rd'
            
            # Title and company
            elif current and 'StaticText' in line and '@' not in current.get('company', ''):
                text = re.search(r'StaticText "(.*?)"', line)
                if text:
                    content = text.group(1)
                    if '@' in content:
                        parts = content.split('@')
                        current['title'] = parts[0].strip()
                        current['company'] = parts[1].strip()
                    elif 'title' not in current:
                        current['title'] = content
            
            if len(contacts) >= limit:
                break
        
        if current and len(contacts) < limit:
            contacts.append(current)
        
        return contacts[:limit]


# Sync wrapper for Streamlit
def search_linkedin_alumni_sync(domain: str, school: str, limit: int = 10) -> List[Dict]:
    """
    Synchronous wrapper for Streamlit
    
    Args:
        domain: Company domain
        school: School name
        limit: Max results
        
    Returns:
        List of contact dictionaries
    """
    automation = LinkedInAutomation()
    return asyncio.run(automation.search_alumni_by_domain(domain, school, limit))


# Demo
if __name__ == "__main__":
    print("🔍 LinkedIn Alumni Search Demo\n")
    
    domain = "shopify.com"
    school = "University of Western Ontario"
    
    print(f"Searching for {school} alumni at {domain}...\n")
    
    contacts = search_linkedin_alumni_sync(domain, school, limit=5)
    
    print(f"\n✅ Found {len(contacts)} contacts:\n")
    
    for i, contact in enumerate(contacts, 1):
        print(f"{i}. {contact.get('name', 'Unknown')}")
        print(f"   Title: {contact.get('title', 'N/A')}")
        print(f"   Company: {contact.get('company', 'N/A')}")
        print(f"   Degree: {contact.get('connection_degree', 'N/A')}")
        print(f"   URL: {contact.get('linkedin_url', 'N/A')}")
        print(f"   Method: {contact.get('search_method', 'N/A')}\n")
