import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from .base_agent import BaseAgent

class CrawlerAgent(BaseAgent):
    def __init__(self):
        super().__init__("CrawlerAgent")
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl the target URL and extract interactive elements"""
        url = state.get("target_url")
        if not url:
            raise ValueError("No target URL provided in state")
            
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract interactive elements
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            forms = [form for form in soup.find_all('form')]
            buttons = [button for button in soup.find_all(['button', 'input[type="submit"]'])]
            
            # Update state with findings
            state.update({
                "page_content": response.text,
                "links": links,
                "forms": forms,
                "buttons": buttons,
                "current_url": url
            })
            
            self.logger.info(f"Successfully crawled {url}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")
            state["error"] = str(e)
            return state 