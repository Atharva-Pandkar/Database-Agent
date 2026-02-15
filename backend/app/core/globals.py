"""Global instances for the application."""
from typing import Optional
from app.services.guardrail import GuardrailService
from app.workflows.main import AgentWorkflow
from app.services.checkpoint import CheckpointService
# Global instances
guardrail: Optional[GuardrailService] = None
workflow: Optional[AgentWorkflow] = None
checkpoint: Optional[CheckpointService] = None
def init_globals():
    """Initialize global instances."""
    global guardrail, workflow, checkpoint
    
    if guardrail is None:
        guardrail = GuardrailService()
    
    if workflow is None:
        workflow = AgentWorkflow()
    if checkpoint is None:
        checkpoint = CheckpointService()
        
def get_guardrail() -> GuardrailService:
    """Get the global guardrail service instance."""
    if guardrail is None:
        raise RuntimeError("GuardrailService not initialized")
    return guardrail

def get_workflow() -> AgentWorkflow:
    """Get the global workflow instance."""
    if workflow is None:
        raise RuntimeError("AgentWorkflow not initialized")
    return workflow

def get_checkpoint() -> CheckpointService:
    """Get the global checkpoint instance."""
    if checkpoint is None:
        raise RuntimeError("CheckpointService not initialized")
    return checkpoint