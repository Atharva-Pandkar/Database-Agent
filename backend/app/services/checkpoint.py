from typing import Dict, Any

class CheckpointService:
    def __init__(self):
        self.state_checkpoint = {}
        self.message_checkpoint = {}

    def save_state(self, state: Dict[str, Any]):
        self.state_checkpoint[state["task_graph_id"]] = state

    def get_state(self, task_graph_id: str) -> Dict[str, Any]:
        return self.state_checkpoint.get(task_graph_id, None)

    def clear_state(self, task_graph_id: str):
        self.state_checkpoint[task_graph_id] = None

    def save_message(self, checkpoint_id: str, message: Dict[str, Any]):
        if self.message_checkpoint.get(checkpoint_id) is not None:
            self.message_checkpoint[checkpoint_id].append(message)
        else:
            self.message_checkpoint[checkpoint_id] = [message]

    def get_message(self, id: str) -> Dict[str, Any]:
        return self.message_checkpoint.get(id, None)

    def clear_message(self, id: str):
        self.message_checkpoint[id] = None