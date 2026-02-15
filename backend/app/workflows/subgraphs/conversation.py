from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

from app.schemas.state import AgentState, ExecutionStatus
from app.workflows.base import BaseNode
from openai import OpenAI
from dotenv import load_dotenv
import os

class DraftAnswer(BaseNode):
    system_prompt_general = """
    You are a helpful assistant that can answer questions and help with tasks.
    Your job is to given an answer to the user's question.
    Users question is: {question}
    The evidence is:
    {evidence}
    Your answer should answer the user's query based on the complied answers and evidence.
    Only give your answer in string format.
    If it is a general question, answer in a sentence and add you are here to help with game queries.
    """

    @staticmethod
    async def process(state: AgentState, config: RunnableConfig) -> AgentState:
        load_dotenv()
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        evidance = ""
        for x in state.collected_evidence:
            for key, value in x.items():
                evidance += f"{key}: {value}\n"
        prompt = DraftAnswer.system_prompt_general.format(question=state.task_graph.query,
                                                   evidence=evidance)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": state.task_graph.query}
            ]
        )
        state.current_task.result = response.choices[0].message.content
        state.final_answer = response.choices[0].message.content
        state.current_task.status = ExecutionStatus.SUCCESS
        return state

class CitationAdder(BaseNode):
    system_prompt_citation = """
    You are a helpful assistant that can check if any citations are provided.
    if any citations are provided in the evidance, you should add them to the answer. 
    Have structured citations to the answer.
    User's question is: {question}
    The evidence is:
    {evidence}
    Answer genrated by previous model is:
    {answer}
    You should add the citations to the answer.
    Only give your answer in string format.
    If it is a general question, answer in a sentence and add you are here to help with game queries.
    
    """
    @staticmethod
    async def process(state: AgentState, config: RunnableConfig) -> AgentState:
        load_dotenv()
        evidance = ""
        for x in state.collected_evidence:
            for key, value in x.items():
                evidance += f"{key}: {value}\n"

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = CitationAdder.system_prompt_citation.format(question=state.task_graph.query,
                                                   evidence=evidance, answer=state.current_task.result)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": state.task_graph.query}
            ]
        )
        state.current_task.result = response.choices[0].message.content
        state.final_answer = response.choices[0].message.content
        if state.current_task:
            state.current_task.status = ExecutionStatus.SUCCESS
        
        # For now just doing this 
        state.completed_tasks[state.current_task.task_node.id] = state.current_task
        state.current_task = None
        
        return state

    
def create_conversation_graph() -> StateGraph:
    """Creates the conversation subgraph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("draft", DraftAnswer.process)
    workflow.add_node("cite", CitationAdder.process)
    
    # Add edges
    workflow.add_edge("draft", "cite")
    
    # Set entry point
    workflow.set_entry_point("draft")
    
    graph = workflow.compile()
    return graph