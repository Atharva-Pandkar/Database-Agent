from typing import Annotated, Any, Dict, List, Tuple, Union
from langchain_core.runnables import RunnableConfig

from app.schemas.state import AgentState, TaskExecutionState
from app.schemas.helpers import SubgraphType, ExecutionStatus
from app.workflows.base import BaseNode
from app.schemas.decomposer import TaskNode
from app.core.logger import logger

class Router(BaseNode):
    """Routes tasks to appropriate subgraphs based on task parameters."""
    
    @staticmethod
    async def get_next_task(state: AgentState) -> Union[str, None]:
        """Get next executable task based on dependencies."""
        if state.task_graph is None or state.task_graph.tasks is None:
            return None
        if not state.task_graph.tasks:  # No more tasks
            return None
        logger.info(f"Getting next task: {state.task_graph}","router/get_next_task")
        next_task_id = state.task_graph.tasks[0].id
        return next_task_id
    
    @staticmethod
    async def check_completed_tasks(state: AgentState) -> bool:
        """Check if current task is completed and can proceed to next."""
        # Initial state has no current task
        if state.current_task is None:
            return True
        
        # Task is completed, can proceed (subgraphs use SUCCESS or COMPLETED)
        if state.current_task.status in (ExecutionStatus.COMPLETED, ExecutionStatus.SUCCESS):
            return True
        
        # Task is still running
        if state.current_task.status == ExecutionStatus.RUNNING:
            return False
        
        # Handle retry/failed cases
        if state.current_task.status in [ExecutionStatus.RETRY, ExecutionStatus.FAILED]:
            state.current_task.retry_count += 1
            state.current_task.status = ExecutionStatus.PENDING
            state.task_graph.tasks.append(state.current_task.task_node)
            return True
            
        return False
    
    @staticmethod
    async def process(state: AgentState, config: RunnableConfig) -> AgentState:
        """Process current state and route to next node."""
        logger.info(f"Router processing state: {state}", "router/process")
        
        proceed = await Router.check_completed_tasks(state)
        if proceed:
            next_task_id = await Router.get_next_task(state)
            
            if next_task_id is None:
                logger.info("No more tasks, ending workflow", "router/process")
                return state
                
            task = state.task_graph.tasks.pop(0)
            if state.current_task is not None:
                state.completed_tasks[state.current_task.task_node.id] = state.current_task
                
            state.current_task = TaskExecutionState(
                task_node=task,
                status=ExecutionStatus.RUNNING,
                retry_count=0,
                result=None,
                error=None
            )
            
            logger.info(f"Routing to subgraph: {task.subgraph_type}", "router/process")
            return state
            
        return state