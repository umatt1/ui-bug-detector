import os
from datetime import datetime
from typing import Dict, Any
from PIL import Image
from .base_agent import BaseAgent

class DetectorAgent(BaseAgent):
    def __init__(self, reports_dir: str = "reports"):
        super().__init__("DetectorAgent")
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Detect bugs by analyzing console logs and taking screenshots"""
        try:
            driver = state.get("driver")
            if not driver:
                raise ValueError("No Selenium driver found in state")
                
            # Capture console logs
            console_logs = driver.get_log('browser')
            errors = [log for log in console_logs if log['level'] == 'SEVERE']
            
            # Take screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.reports_dir, f"screenshot_{timestamp}.png")
            driver.save_screenshot(screenshot_path)
            
            # Analyze screenshot for visual issues (placeholder)
            # In a real implementation, you might compare with baseline images
            # or use computer vision to detect obvious visual bugs
            
            # Update state with findings
            state.update({
                "console_logs": console_logs,
                "errors": errors,
                "screenshot_path": screenshot_path,
                "bugs_detected": len(errors) > 0
            })
            
            if errors:
                self.logger.warning(f"Detected {len(errors)} console errors")
            else:
                self.logger.info("No console errors detected")
                
            return state
            
        except Exception as e:
            self.logger.error(f"Error during detection: {str(e)}")
            state["error"] = str(e)
            return state 