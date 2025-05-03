from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, Any
from .base_agent import BaseAgent

class InteractionAgent(BaseAgent):
    def __init__(self):
        super().__init__("InteractionAgent")
        self.driver = None
        
    def setup_driver(self):
        """Initialize headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Interact with the page using Selenium"""
        if not self.driver:
            self.setup_driver()
            
        try:
            url = state.get("current_url")
            self.driver.get(url)
            
            # Record initial state
            actions = []
            
            # Click buttons
            for button in state.get("buttons", []):
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{button.text}')]"))
                    )
                    element.click()
                    actions.append({"type": "click", "element": button.text})
                except Exception as e:
                    self.logger.warning(f"Could not click button {button.text}: {str(e)}")
            
            # Fill forms
            for form in state.get("forms", []):
                try:
                    inputs = form.find_all("input")
                    for input_field in inputs:
                        if input_field.get("type") != "submit":
                            element = self.driver.find_element(By.NAME, input_field.get("name"))
                            element.send_keys("test_data")
                            actions.append({
                                "type": "input",
                                "element": input_field.get("name"),
                                "value": "test_data"
                            })
                except Exception as e:
                    self.logger.warning(f"Could not fill form: {str(e)}")
            
            state["actions"] = actions
            return state
            
        except Exception as e:
            self.logger.error(f"Error during interaction: {str(e)}")
            state["error"] = str(e)
            return state
            
    def __del__(self):
        """Clean up Selenium driver"""
        if self.driver:
            self.driver.quit() 