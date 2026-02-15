import uuid
from fastapi import APIRouter, Request, Depends
from ..schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
from ..schemas.decomposer import TaskGraph
from ..services.decomposer import DecomposerService
from ..core.globals import get_guardrail, get_workflow
from ..core.logger import logger
router = APIRouter()
 
chat_history: list[ChatMessageResponse] = []

async def get_decomposer_service():
    return DecomposerService()

@router.post("/message", response_model=ChatMessageResponse)
async def process_message(
    request: Request, 
    chat_message: ChatMessageRequest,
    decomposer: DecomposerService = Depends(get_decomposer_service)
) -> ChatMessageResponse:
    """Process a chat message using the workflow"""
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    try:
        # Decompose the message into tasks
        config = {"configurable": {"thread_id": correlation_id}}
        if not get_guardrail().check_input_query(chat_message.message):
            return ChatMessageResponse(
                id=str(uuid.uuid4()),
                message=chat_message.message,
                response="I apologize, I couldn't process your request.",
                task_graph=None
            )
        task_graph = await decomposer.decompose_query(chat_message.message)
        logger.info(f"Initial task graph: {task_graph}", "chat_router/process_message")
        
        # Create workflow input
        workflow_input = {
            "task_graph_id": str(uuid.uuid4()),
            "task_graph": task_graph,
            "max_retries": 2
        }
        
        # Run workflow
        final_state = await get_workflow().run_agent(workflow_input, config)
        logger.info(f"Final state: check completed tasks {final_state}", "chat_router/process_message")
        
        # Extract final answer from conversation results
        final_answer = final_state.final_answer
        answer = get_guardrail().check_output_query(chat_message.message, final_state)
        if answer.get("status") == "VALID":
            logger.info(f"Final answer: {final_state}", "chat_router/process_message")
            final_answer = final_state.final_answer
        else:
            final_answer = "I apologize, I couldn't process your request."
        # Create response
        response = ChatMessageResponse(
            id=str(uuid.uuid4()),
            message=chat_message.message,
            response=final_answer,
            task_graph=final_state.task_graph
        )
        
        # Store in chat history
        chat_history.append(response)
        
        logger.info(
            message="Chat message processed successfully",
            component="chat_router",
            extras={"correlation_id": correlation_id}
        )
        
        return response
        
    except Exception as e:
        logger.error(
            message="Error processing chat message",
            component="chat_router",
            extras={"error": str(e)},
            correlation_id=correlation_id
        )
        raise

@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(request: Request) -> ChatHistoryResponse:
    """
    Retrieve chat history
    """
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    logger.info(
        message="Retrieving chat history",
        component="chat_router",
        extras={"history_length": len(chat_history)},
        correlation_id=correlation_id
    )
    
    return ChatHistoryResponse(messages=chat_history)