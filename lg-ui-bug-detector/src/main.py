import os
import argparse
import logging
import time
from typing import Dict, Any, TypedDict, List, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from agents.crawler_agent import CrawlerAgent
from agents.interaction_agent import InteractionAgent
from agents.detector_agent import DetectorAgent
from agents.reproducer_agent import ReproducerAgent
from agents.explainer_agent import ExplainerAgent

# Setup logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ui_bug_detector.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom exception for timeout handling"""
    pass

class AgentState(TypedDict):
    target_url: str
    username: Optional[str]
    password: Optional[str]
    current_url: Optional[str]
    page_content: Optional[str]
    links: Optional[List[str]]
    forms: Optional[List[Any]]
    buttons: Optional[List[Any]]
    actions: Optional[List[Dict[str, Any]]]
    driver: Optional[Any]
    console_logs: Optional[List[Dict[str, Any]]]
    errors: Optional[List[Dict[str, Any]]]
    screenshot_path: Optional[str]
    bugs_detected: Optional[bool]
    reproduction_script: Optional[str]
    bug_report: Optional[str]
    error: Optional[str]
    start_time: Optional[float]
    llm_calls: Optional[int]

def create_workflow() -> StateGraph:
    """Create and configure the LangGraph workflow"""
    logger.info("Initializing workflow...")
    
    # Initialize agents
    crawler = CrawlerAgent()
    interactor = InteractionAgent()
    detector = DetectorAgent()
    reproducer = ReproducerAgent()
    explainer = ExplainerAgent()
    
    # Create workflow with state schema
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("crawl", crawler.get_node())
    workflow.add_node("interact", interactor.get_node())
    workflow.add_node("detect", detector.get_node())
    workflow.add_node("reproduce", reproducer.get_node())
    workflow.add_node("explain", explainer.get_node())
    
    # Define edges
    workflow.add_edge("crawl", "interact")
    workflow.add_edge("interact", "detect")
    workflow.add_edge("detect", "reproduce")
    workflow.add_edge("reproduce", "explain")
    workflow.add_edge("explain", END)
    
    # Set entry point
    workflow.set_entry_point("crawl")
    
    logger.info("Workflow initialized successfully")
    return workflow

def check_timeout(state: AgentState, max_duration: int = 300) -> None:
    """Check if the execution has exceeded the maximum duration"""
    if not state.get("start_time"):
        return
        
    elapsed_time = time.time() - state["start_time"]
    if elapsed_time > max_duration:
        raise TimeoutError(f"Execution exceeded maximum duration of {max_duration} seconds")

def main():
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UI Bug Detector")
    parser.add_argument("url", help="Target URL to analyze")
    parser.add_argument("--username", help="Username for authentication (optional)")
    parser.add_argument("--password", help="Password for authentication (optional)")
    parser.add_argument("--timeout", type=int, default=300, help="Maximum execution time in seconds (default: 300)")
    parser.add_argument("--max-llm-calls", type=int, default=10, help="Maximum number of LLM calls (default: 10)")
    args = parser.parse_args()
    
    logger.info(f"Starting analysis of URL: {args.url}")
    logger.info(f"Timeout set to {args.timeout} seconds")
    logger.info(f"Maximum LLM calls set to {args.max_llm_calls}")
    
    # Create initial state
    initial_state: AgentState = {
        "target_url": args.url,
        "username": args.username,
        "password": args.password,
        "current_url": None,
        "page_content": None,
        "links": None,
        "forms": None,
        "buttons": None,
        "actions": None,
        "driver": None,
        "console_logs": None,
        "errors": None,
        "screenshot_path": None,
        "bugs_detected": None,
        "reproduction_script": None,
        "bug_report": None,
        "error": None,
        "start_time": time.time(),
        "llm_calls": 0
    }
    
    try:
        # Create and run workflow
        workflow = create_workflow()
        app = workflow.compile()
        
        # Execute workflow with timeout checking
        logger.info("Starting workflow execution...")
        final_state = app.invoke(initial_state)
        
        # Print results
        if final_state.get("error"):
            logger.error(f"Error during execution: {final_state['error']}")
        else:
            elapsed_time = time.time() - final_state["start_time"]
            logger.info(f"Analysis completed successfully in {elapsed_time:.2f} seconds")
            logger.info(f"Total LLM calls: {final_state.get('llm_calls', 0)}")
            
            if final_state.get("bug_report"):
                logger.info(f"Bug report generated at: {final_state['bug_report']}")
            if final_state.get("reproduction_script"):
                logger.info(f"Reproduction script generated at: {final_state['reproduction_script']}")
                
    except TimeoutError as e:
        logger.error(f"Timeout error: {str(e)}")
        logger.error("Execution was terminated due to timeout")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
    finally:
        # Cleanup
        if "driver" in final_state and final_state["driver"]:
            try:
                final_state["driver"].quit()
                logger.info("Selenium driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing Selenium driver: {str(e)}")

if __name__ == "__main__":
    main() 