import os
import time
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json
from datetime import datetime
from .base_agent import BaseAgent

class ExplainerAgent(BaseAgent):
    def __init__(self):
        super().__init__("ExplainerAgent")
        self.llm = ChatOpenAI(temperature=0)
        
    def format_bug_report(self, bugs: List[Dict[str, Any]], console_errors: List[str], actions: List[Dict[str, Any]]) -> str:
        """Format the bug report with better organization and details"""
        report = []
        
        # Add header
        report.append("# UI Bug Report")
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Summary section
        report.append("## Summary")
        report.append(f"Total bugs found: {len(bugs)}")
        if console_errors:
            report.append(f"Console errors: {len(console_errors)}")
        report.append(f"Total interactions: {len(actions)}\n")
        
        # Console Errors section
        if console_errors:
            report.append("## Console Errors")
            for i, error in enumerate(console_errors, 1):
                report.append(f"### Error {i}")
                report.append(f"```\n{error}\n```\n")
        
        # Bug Details section
        if bugs:
            report.append("## Bug Details")
            for i, bug in enumerate(bugs, 1):
                report.append(f"### Bug {i}: {bug.get('title', 'Untitled Bug')}")
                
                # Bug description
                report.append("#### Description")
                report.append(f"{bug.get('description', 'No description provided')}\n")
                
                # Bug severity
                if 'severity' in bug:
                    report.append("#### Severity")
                    report.append(f"{bug['severity']}\n")
                
                # Bug location
                if 'location' in bug:
                    report.append("#### Location")
                    report.append(f"{bug['location']}\n")
                
                # Bug reproduction steps
                if 'reproduction_steps' in bug:
                    report.append("#### Reproduction Steps")
                    for j, step in enumerate(bug['reproduction_steps'], 1):
                        report.append(f"{j}. {step}")
                    report.append("")
                
                # Bug impact
                if 'impact' in bug:
                    report.append("#### Impact")
                    report.append(f"{bug['impact']}\n")
                
                # Bug recommendations
                if 'recommendations' in bug:
                    report.append("#### Recommendations")
                    for j, rec in enumerate(bug['recommendations'], 1):
                        report.append(f"{j}. {rec}")
                    report.append("")
        
        # Interaction Log section
        if actions:
            report.append("## Interaction Log")
            for i, action in enumerate(actions, 1):
                action_type = action.get('type', 'unknown')
                element = action.get('element', 'unknown')
                report.append(f"{i}. {action_type.capitalize()}: {element}")
                if 'value' in action:
                    report.append(f"   Value: {action['value']}")
                if 'href' in action:
                    report.append(f"   URL: {action['href']}")
                report.append("")
        
        return "\n".join(report)
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed explanation of the bugs found"""
        try:
            # Check if we've hit the LLM call limit
            if state.get("llm_calls", 0) >= state.get("max_llm_calls", 10):
                self.logger.warning("Maximum LLM calls reached, skipping explanation generation")
                state["bug_report"] = "Maximum LLM calls reached. Please check the logs for details."
                return state
                
            console_errors = state.get("console_logs", [])
            actions = state.get("actions", [])
            bugs = state.get("bugs_detected", [])
            
            self.logger.info(f"Generating bug report for {len(bugs)} bugs, {len(console_errors)} console errors, and {len(actions)} actions")
            
            # Create a prompt template for bug explanation
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert UI/UX bug analyzer. Your task is to analyze the detected bugs, console errors, and user interactions to provide a comprehensive bug report.
                
                For each bug, provide:
                1. A clear, concise title
                2. A detailed description of the issue
                3. The severity level (Critical, High, Medium, Low)
                4. The exact location where the bug occurs
                5. Step-by-step reproduction steps
                6. The impact on user experience
                7. Specific recommendations for fixing the issue
                
                Format your response as a JSON object with the following structure:
                {
                    "bugs": [
                        {
                            "title": "string",
                            "description": "string",
                            "severity": "string",
                            "location": "string",
                            "reproduction_steps": ["string"],
                            "impact": "string",
                            "recommendations": ["string"]
                        }
                    ]
                }"""),
                ("user", """Please analyze the following information and generate a detailed bug report:

                Console Errors:
                {console_errors}

                User Actions:
                {actions}

                Detected Bugs:
                {bugs}

                Provide a comprehensive analysis of each bug, including its severity, impact, and recommendations for fixing it.""")
            ])
            
            # Format the input data
            console_errors_str = "\n".join(console_errors) if console_errors else "No console errors found"
            actions_str = json.dumps(actions, indent=2)
            bugs_str = json.dumps(bugs, indent=2)
            
            # Generate the explanation
            self.logger.info("Generating bug report using LLM...")
            start_time = time.time()
            chain = prompt | self.llm
            result = chain.invoke({
                "console_errors": console_errors_str,
                "actions": actions_str,
                "bugs": bugs_str
            })
            
            # Parse the response
            try:
                bug_analysis = json.loads(result.content)
                bugs = bug_analysis.get("bugs", [])
                
                # Format the complete report
                report = self.format_bug_report(bugs, console_errors, actions)
                
                # Save the report
                os.makedirs("reports", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = f"reports/bug_report_{timestamp}.md"
                
                with open(report_path, "w") as f:
                    f.write(report)
                
                self.logger.info(f"Bug report saved to {report_path}")
                
                # Update state
                state["bug_report"] = report
                state["llm_calls"] = state.get("llm_calls", 0) + 1
                
                self.logger.info(f"Generated bug report in {time.time() - start_time:.2f} seconds")
                return state
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {str(e)}")
                state["error"] = f"Failed to parse bug report: {str(e)}"
                return state
                
        except Exception as e:
            self.logger.error(f"Error generating bug report: {str(e)}")
            state["error"] = str(e)
            return state 