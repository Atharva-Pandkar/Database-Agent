from typing import Tuple
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

from app.schemas.state import AgentState, ExecutionStatus
from app.workflows.base import BaseNode
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()
class WebSearchNode(BaseNode):
    @staticmethod
    async def process(state: AgentState, config: RunnableConfig) -> AgentState:
        """Perform web search and process results."""
        # TODO: Implement web search logic
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type":"web_search_preview"}],
            input=[
                {"role": "system", "content": "You are a helpful assistant that can answer questions and help with tasks. For all searches you do you will provide a list of citations"},
                {"role": "user", "content": state.current_task.task_node.description}
            ]
        )
        if state.current_task:
            state.current_task.status = ExecutionStatus.COMPLETED
            state.current_task.result = response.output_text
            state.collected_evidence.append({"web_search_result": response.output_text})
            state.web_search_used = True
            state.completed_tasks[state.current_task.task_node.id] = state.current_task
            state.current_task = None
        
        return state

def create_web_search_graph() -> StateGraph:
    """Creates the web search subgraph."""
    workflow = StateGraph(AgentState)
    
    # Add node
    workflow.add_node("search", WebSearchNode.process)
    
    # Set entry point
    workflow.set_entry_point("search")
    
    graph = workflow.compile()
    return graph