from typing import Tuple
from langchain_core.runnables import RunnableConfig

from app.schemas.state import AgentState, ExecutionStatus    
from app.workflows.base import BaseNode

class RetryNode(BaseNode):
    """Handles retry logic for failed tasks."""
    
    @staticmethod
    async def validate_state(state: AgentState) -> bool:
        return (
            state.current_task is not None and 
            state.current_task.status == ExecutionStatus.FAILED
        )
    
    @staticmethod
    async def process(state: AgentState, config: RunnableConfig) -> Tuple[str, AgentState]:
        """Process retry logic."""
        if not state.current_task:
            return  state
            
        if state.current_task.retry_count >= state.max_retries:
            # Mark task as permanently failed
            state.current_task.status = ExecutionStatus.FAILED
            
            # Store failed state
            state.completed_tasks[state.current_task.task_id] = state.current_task
            state.current_task = None
            
            return  state
            
        # Increment retry counter
        state.current_task.retry_count += 1
        state.current_task.status = ExecutionStatus.RETRYING
        state.task_graph.tasks.append(state.current_task)
        state.current_task.result = None
        
        return  state
