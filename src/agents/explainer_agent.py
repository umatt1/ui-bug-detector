import os
import time
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent

class ExplainerAgent(BaseAgent):
    def __init__(self, reports_dir: str = "reports"):
        super().__init__("ExplainerAgent")
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
        self.llm = ChatOpenAI(temperature=0)
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a human-readable explanation of detected bugs"""
        try:
            if not state.get("bugs_detected"):
                self.logger.info("No bugs detected, skipping explanation")
                return state
                
            # Check LLM call limit
            llm_calls = state.get("llm_calls", 0)
            max_llm_calls = state.get("max_llm_calls", 10)
            
            if llm_calls >= max_llm_calls:
                self.logger.warning(f"Maximum LLM calls ({max_llm_calls}) reached, skipping explanation")
                state["error"] = "Maximum LLM calls reached"
                return state
                
            # Prepare bug information
            errors = state.get("errors", [])
            screenshot_path = state.get("screenshot_path")
            actions = state.get("actions", [])
            
            self.logger.info("Preparing to generate bug explanation...")
            self.logger.info(f"Found {len(errors)} console errors")
            self.logger.info(f"Recorded {len(actions)} actions")
            
            # Create prompt template
            template = """You are a UI bug detection expert. Please analyze the following bug information and provide a clear, concise explanation:

Console Errors:
{errors}

Actions Performed:
{actions}

Screenshot Path:
{screenshot_path}

Please provide:
1. A summary of the bug
2. The likely cause
3. Potential impact
4. Suggested fixes

Keep the explanation clear and actionable."""
            
            prompt = ChatPromptTemplate.from_template(template)
            
            # Format the prompt
            formatted_prompt = prompt.format_messages(
                errors="\n".join([f"- {error['message']}" for error in errors]),
                actions="\n".join([f"- {action['type']}: {action['element']}" for action in actions]),
                screenshot_path=screenshot_path
            )
            
            # Generate explanation with timing
            start_time = time.time()
            self.logger.info("Calling LLM for explanation...")
            explanation = self.llm.invoke(formatted_prompt)
            elapsed_time = time.time() - start_time
            
            # Update LLM call count
            state["llm_calls"] = llm_calls + 1
            
            self.logger.info(f"LLM call completed in {elapsed_time:.2f} seconds")
            self.logger.info(f"Total LLM calls: {state['llm_calls']}")
            
            # Save explanation to file
            report_path = os.path.join(self.reports_dir, "bug_report.md")
            with open(report_path, "w") as f:
                f.write("# Bug Report\n\n")
                f.write(explanation.content)
                
            state["bug_report"] = report_path
            self.logger.info(f"Generated bug report at {report_path}")
            return state
            
        except Exception as e:
            self.logger.error(f"Error generating explanation: {str(e)}")
            state["error"] = str(e)
            return state 