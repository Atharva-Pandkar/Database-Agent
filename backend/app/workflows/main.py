from typing import Dict, Any
from app.core.logger import logger
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig
from app.schemas.state import AgentState
from app.workflows.router import Router
from app.workflows.retry import RetryNode
from app.schemas.helpers import SubgraphType, ExecutionStatus
from app.workflows.subgraphs.db_search import create_db_search_graph
from app.workflows.subgraphs.web_search import create_web_search_graph
from app.workflows.subgraphs.db_update import create_db_update_graph
from app.workflows.subgraphs.conversation import create_conversation_graph
from langgraph.checkpoint.memory import MemorySaver

def end_node(state: AgentState) -> AgentState:
    """End node that returns the final state."""
    return state

class AgentWorkflow:
    """Main agent workflow that orchestrates all subgraphs."""
    
    def __init__(self):
        self.graph = self.create_agent_workflow_compiled()
    
    def create_agent_workflow_compiled(self) -> StateGraph:
        """Creates the main agent workflow graph."""
        
        # Create main workflow
        workflow = StateGraph(AgentState)

        # Add router node
        workflow.add_node("router", Router.process)
        # Add retry node
        workflow.add_node("retry", RetryNode.process)
        db_search_graph = create_db_search_graph()
        web_search_graph = create_web_search_graph()
        db_update_graph = create_db_update_graph()
        conversation_graph = create_conversation_graph()
        # Create and add subgraphs
        subgraphs = {
            SubgraphType.DB_SEARCH.value: db_search_graph,
            SubgraphType.WEB_SEARCH.value: web_search_graph,
            SubgraphType.DB_UPDATE.value: db_update_graph,
            SubgraphType.CONVERSATION.value: conversation_graph
        }
        
        # Add nodes
        for name, subgraph in subgraphs.items():
            workflow.add_node(name, subgraph)
            workflow.add_edge(name, "router")
            workflow.add_conditional_edges(name, self.retry_to_router, {
                "router": "router",
                "retry": "retry",
            })
        # Add conditional edges from router to subgraphs
        workflow.add_conditional_edges(
            "router",
            self.router_to_subgraph,
            {
                SubgraphType.DB_SEARCH.value: "db_search",
                SubgraphType.WEB_SEARCH.value: "web_search",
                SubgraphType.DB_UPDATE.value: "db_update",
                SubgraphType.CONVERSATION.value: "conversation",
                "end": "end",
            }
        )
        
       

        # Add retry edge back to router
        workflow.add_edge("retry", "router")
        
        # Add end node
        workflow.add_node("end", end_node)
        
        # Set entry point
        workflow.set_entry_point("router")
        # checkpoint = MemorySaver()
        # graph = workflow.compile(checkpointer=checkpoint)
        graph = workflow.compile()
        image = graph.get_graph().draw_ascii()
        print(image)
        return graph
    def retry_to_router(self, state: AgentState):
        
        if state.current_task is None:
            return "router"
        if state.current_task.status == ExecutionStatus.RETRY:
            return "retry"
        return "end"
    def router_to_subgraph(self, state: AgentState):
        
        if not state.current_task:
            return "end"
        
        if state.current_task.task_node.subgraph_type == SubgraphType.DB_SEARCH:
            return "db_search"
        
        if state.current_task.task_node.subgraph_type == SubgraphType.WEB_SEARCH:
            return "web_search"
        
        if state.current_task.task_node.subgraph_type == SubgraphType.DB_UPDATE:
            return "db_update"
        
        if state.current_task.task_node.subgraph_type == SubgraphType.CONVERSATION:
            return "conversation"
        
        return "end"

    async def run_agent(
        self,
        task_input: Dict[str, Any],
        config: RunnableConfig
    ) -> AgentState:
        """
        Runs the agent workflow with given input.
        
        Args:
            task_input: Dictionary containing task graph and other inputs
            config: Configuration for the runnable
            
        Returns:
            Final state after workflow completion
        """
        # Create initial state
        initial_state = AgentState(**task_input)
        
        # Run workflow
        final_state = await self.graph.ainvoke(initial_state, config)
        
        return final_state