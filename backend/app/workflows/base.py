from typing import Any, Dict, List
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from app.schemas.state import AgentState, TaskExecutionState, ExecutionStatus
from app.schemas.decomposer import TaskGraph

class BaseNode:
    """Base class for all nodes in the workflow."""
    
    @staticmethod
    async def validate_state(state: AgentState) -> bool:
        """Validate if the state is ready for this node."""
        raise NotImplementedError
    
    @staticmethod
    async def process(state: AgentState, config: RunnableConfig) -> AgentState:
        """Process the state and return updated state."""
        raise NotImplementedError

    @staticmethod
    async def handle_error(state: AgentState, error: Exception) -> AgentState:
        """Handle any errors during processing."""
        if state.current_task:
            state.current_task.status = ExecutionStatus.FAILED
            state.current_task.error = str(error)
        return state
