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
        try:
            if not self.driver:
                self.logger.info("Setting up Selenium driver...")
                self.setup_driver()
                
            url = state.get("current_url")
            self.logger.info(f"Navigating to URL: {url}")
            self.driver.get(url)
            
            # Record initial state
            actions = []
            
            # Click buttons
            for button in state.get("buttons", []):
                try:
                    self.logger.info(f"Attempting to click button: {button.text}")
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{button.text}')]"))
                    )
                    element.click()
                    actions.append({"type": "click", "element": button.text})
                    self.logger.info(f"Successfully clicked button: {button.text}")
                except Exception as e:
                    self.logger.warning(f"Could not click button {button.text}: {str(e)}")
            
            # Fill forms
            for form in state.get("forms", []):
                try:
                    inputs = form.find_all("input")
                    for input_field in inputs:
                        if input_field.get("type") != "submit":
                            self.logger.info(f"Attempting to fill input: {input_field.get('name')}")
                            element = self.driver.find_element(By.NAME, input_field.get("name"))
                            element.send_keys("test_data")
                            actions.append({
                                "type": "input",
                                "element": input_field.get("name"),
                                "value": "test_data"
                            })
                            self.logger.info(f"Successfully filled input: {input_field.get('name')}")
                except Exception as e:
                    self.logger.warning(f"Could not fill form: {str(e)}")
            
            # Add driver to state
            state["driver"] = self.driver
            state["actions"] = actions
            
            self.logger.info(f"Completed {len(actions)} interactions")
            return state
            
        except Exception as e:
            self.logger.error(f"Error during interaction: {str(e)}")
            state["error"] = str(e)
            return state
            
    def __del__(self):
        """Clean up Selenium driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Selenium driver closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing Selenium driver: {str(e)}") 