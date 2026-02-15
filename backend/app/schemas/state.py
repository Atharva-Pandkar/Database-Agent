from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from app.schemas.decomposer import TaskGraph, TaskNode
from app.schemas.helpers import SubgraphType, ExecutionStatus, TaskStatus


class TaskExecutionState(BaseModel):
    retry_count: int = Field(default=0, description="Number of times the task has been retried")
    status: ExecutionStatus = Field(..., description="Current status of the task")
    task_node: TaskNode = Field(..., description="Task node")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Result of the task")
    error: Optional[str] = Field(default=None, description="Error message if the task failed")

class AgentState(BaseModel):
    task_graph_id: str = Field(..., description="Unique identifier for the task graph")
    task_graph: TaskGraph = Field(..., description="Task graph")
    current_task: Optional[TaskExecutionState] = Field(default=None, description="Current task being executed")
    completed_tasks: Dict[str, TaskExecutionState] = Field(
        default_factory=dict, 
        description="Map of task_id to execution state for completed tasks"
    )
    collected_evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Evidence collected during task execution for final response"
    )
    max_retries: int = Field(default=3, description="Maximum number of retries per task")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    db_search_used: bool = Field(default=False, description="Whether the database search was used")
    web_search_used: bool = Field(default=False, description="Whether the web search was used")
    db_update_used: bool = Field(default=False, description="Whether the database update was used")
    db_result: Dict[str, TaskExecutionState] = Field(default_factory=dict, description="Result of the database search")
    web_result: Dict[str, TaskExecutionState] = Field(default_factory=dict, description="Result of the web search")
    db_update_result: Dict[str, TaskExecutionState] = Field(default_factory=dict, description="Result of the database update")
    final_answer: str = Field(default="", description="Final answer to the user's query")