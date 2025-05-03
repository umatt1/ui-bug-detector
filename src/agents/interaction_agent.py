from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, Any, List
from .base_agent import BaseAgent
import time

class InteractionAgent(BaseAgent):
    def __init__(self):
        super().__init__("InteractionAgent")
        self.driver = None
        self.wait = None
        self.original_window = None
        
    def setup_driver(self):
        """Initialize headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")  # Reduce logging noise
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.original_window = self.driver.current_window_handle
        
    def handle_login(self, state: Dict[str, Any]) -> None:
        """Handle login if credentials are provided"""
        username = state.get("username")
        password = state.get("password")
        
        if username and password:
            self.logger.info("Attempting to log in...")
            try:
                # Wait for login form
                username_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "user-name"))
                )
                password_field = self.driver.find_element(By.ID, "password")
                login_button = self.driver.find_element(By.ID, "login-button")
                
                # Fill in credentials
                username_field.send_keys(username)
                password_field.send_keys(password)
                login_button.click()
                
                # Wait for login to complete
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "inventory_list"))
                )
                self.logger.info("Successfully logged in")
            except Exception as e:
                self.logger.error(f"Login failed: {str(e)}")
                raise

    def safe_click(self, element, max_retries=3):
        """Safely click an element with retries for stale elements and intercepted clicks"""
        for attempt in range(max_retries):
            try:
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)  # Wait for scroll to complete
                
                # Try to click
                element.click()
                return True
            except StaleElementReferenceException:
                self.logger.warning(f"Element became stale, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(0.5)
            except ElementClickInterceptedException:
                self.logger.warning(f"Click intercepted, retrying... (attempt {attempt + 1}/{max_retries})")
                # Try to close any overlays
                try:
                    close_buttons = self.driver.find_elements(By.CLASS_NAME, "bm-cross-button")
                    if close_buttons:
                        close_buttons[0].click()
                        time.sleep(0.5)
                except:
                    pass
            except Exception as e:
                self.logger.warning(f"Click failed: {str(e)}")
                return False
        return False

    def handle_new_tab(self):
        """Handle new tab if opened"""
        if len(self.driver.window_handles) > 1:
            # Switch to new tab
            for window_handle in self.driver.window_handles:
                if window_handle != self.original_window:
                    self.driver.switch_to.window(window_handle)
                    break
            
            # Close new tab and switch back
            self.driver.close()
            self.driver.switch_to.window(self.original_window)
            return True
        return False

    def get_cart_count(self) -> int:
        """Get current number of items in cart"""
        try:
            cart_badge = self.driver.find_element(By.CLASS_NAME, "shopping_cart_badge")
            return int(cart_badge.text)
        except:
            return 0

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Interact with the page using Selenium"""
        try:
            if not self.driver:
                self.logger.info("Setting up Selenium driver...")
                self.setup_driver()
                
            url = state.get("current_url")
            self.logger.info(f"Navigating to URL: {url}")
            self.driver.get(url)
            
            # Handle login if credentials are provided
            self.handle_login(state)
            
            # Record initial state
            actions = []
            
            # Find and interact with elements
            try:
                # Wait for page to load
                self.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Find all interactive elements
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                links = self.driver.find_elements(By.TAG_NAME, "a")
                
                self.logger.info(f"Found {len(buttons)} buttons, {len(inputs)} inputs, {len(links)} links")
                
                # Interact with buttons
                for button in buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text or button.get_attribute('value')
                            
                            # Skip if button is "Remove" and item is not in cart
                            if button_text == "Remove" and self.get_cart_count() == 0:
                                continue
                                
                            # Skip if button is "Add to cart" and item is already in cart
                            if button_text == "Add to cart" and button.get_attribute("data-test") == "remove-sauce-labs-backpack":
                                continue
                                
                            self.logger.info(f"Attempting to click button: {button_text}")
                            if self.safe_click(button):
                                actions.append({
                                    "type": "click",
                                    "element": button_text,
                                    "tag": "button"
                                })
                                self.logger.info("Button clicked successfully")
                                
                                # Handle cart state changes
                                if button_text in ["Add to cart", "Remove"]:
                                    time.sleep(0.5)  # Wait for cart to update
                                    self.logger.info(f"Current cart count: {self.get_cart_count()}")
                    except Exception as e:
                        self.logger.warning(f"Could not click button: {str(e)}")
                
                # Interact with inputs
                for input_field in inputs:
                    try:
                        if input_field.is_displayed() and input_field.is_enabled():
                            input_type = input_field.get_attribute("type")
                            if input_type not in ["submit", "button", "hidden"]:
                                input_name = input_field.get_attribute("name")
                                self.logger.info(f"Attempting to fill input: {input_name}")
                                input_field.send_keys("test_data")
                                actions.append({
                                    "type": "input",
                                    "element": input_name,
                                    "value": "test_data",
                                    "tag": "input"
                                })
                                self.logger.info("Input filled successfully")
                    except Exception as e:
                        self.logger.warning(f"Could not fill input: {str(e)}")
                
                # Interact with links
                for link in links:
                    try:
                        if link.is_displayed() and link.is_enabled():
                            href = link.get_attribute("href")
                            if href and not href.startswith("javascript:"):
                                link_text = link.text.strip()
                                if link_text:  # Only click links with visible text
                                    self.logger.info(f"Attempting to click link: {link_text}")
                                    if self.safe_click(link):
                                        # Handle new tab if opened
                                        if self.handle_new_tab():
                                            self.logger.info("Closed new tab")
                                            
                                        actions.append({
                                            "type": "click",
                                            "element": link_text,
                                            "tag": "link",
                                            "href": href
                                        })
                                        self.logger.info("Link clicked successfully")
                    except Exception as e:
                        self.logger.warning(f"Could not click link: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"Error during element interaction: {str(e)}")
            
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
                # Close all windows
                for window_handle in self.driver.window_handles:
                    self.driver.switch_to.window(window_handle)
                    self.driver.close()
                self.driver.quit()
                self.logger.info("Selenium driver closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing Selenium driver: {str(e)}") 