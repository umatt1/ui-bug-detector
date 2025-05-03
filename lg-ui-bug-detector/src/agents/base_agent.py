from typing import Dict, Any
from langgraph.graph import StateGraph, END
import logging

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Base call method that all agents must implement"""
        raise NotImplementedError("Subclasses must implement __call__")
    
    def get_node(self) -> StateGraph:
        """Returns the LangGraph node for this agent"""
        return self.__call__ 