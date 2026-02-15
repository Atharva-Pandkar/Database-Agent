from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from app.schemas.helpers import SubgraphType, ExecutionStatus


class TaskNode(BaseModel):
    id: str = Field(..., description="Unique identifier for the task")
    title: str = Field(..., description="Short title describing the task")
    description: str = Field(..., description="Detailed description of what needs to be done")
    dependencies: List[str] = Field(default_factory=list, description="IDs of tasks that must be completed before this one")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the task")
    estimated_complexity: int = Field(..., ge=1, le=5, description="Estimated complexity on a scale of 1-5")
    subgraph_type: SubgraphType = Field(..., description="Type of subgraph to use for the task")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="Current status of the task")

class TaskGraph(BaseModel):
    id: str = Field(..., description="Unique identifier for the task graph")
    query: str = Field(..., description="Original user query that generated this task graph")
    tasks: List[TaskNode] = Field(default_factory=list, description="List of tasks in the graph")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the task graph was created")

class DecompositionRequest(BaseModel):
    query: str = Field(..., description="The query to decompose into tasks")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context that might help in decomposing the query"
    )

class DecompositionResponse(BaseModel):
    task_graph: TaskGraph = Field(..., description="The generated task graph")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the decomposition process"
    )
