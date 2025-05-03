import os
from typing import Dict, Any
from .base_agent import BaseAgent

class ReproducerAgent(BaseAgent):
    def __init__(self, reports_dir: str = "reports"):
        super().__init__("ReproducerAgent")
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a reproduction script for detected bugs"""
        try:
            if not state.get("bugs_detected"):
                self.logger.info("No bugs detected, skipping reproduction script")
                return state
                
            actions = state.get("actions", [])
            url = state.get("current_url")
            
            # Generate Python script
            script_content = f'''from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def reproduce_bug():
    # Setup
    chrome_options = Options()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Navigate to URL
        driver.get("{url}")
        
        # Reproduction steps
'''
            
            # Add actions to script
            for action in actions:
                if action["type"] == "click":
                    script_content += f'''
        # Click {action["element"]}
        element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{action["element"]}')]"))
        )
        element.click()
'''
                elif action["type"] == "input":
                    script_content += f'''
        # Fill input {action["element"]}
        element = driver.find_element(By.NAME, "{action["element"]}")
        element.send_keys("{action["value"]}")
'''
            
            # Add cleanup
            script_content += '''
    finally:
        driver.quit()

if __name__ == "__main__":
    reproduce_bug()
'''
            
            # Save script
            script_path = os.path.join(self.reports_dir, "reproduction_script.py")
            with open(script_path, "w") as f:
                f.write(script_content)
                
            state["reproduction_script"] = script_path
            self.logger.info(f"Generated reproduction script at {script_path}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error generating reproduction script: {str(e)}")
            state["error"] = str(e)
            return state 