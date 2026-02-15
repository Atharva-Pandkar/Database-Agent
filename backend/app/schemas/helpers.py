from enum import Enum


class SubgraphType(str, Enum):
    DB_SEARCH = "db_search"
    WEB_SEARCH = "web_search"
    DB_UPDATE = "db_update"
    CONVERSATION = "conversation"

class ExecutionStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SUCCESS = "success"
    RETRY = "retry"
    PENDING = "pending"
    INVALID = "invalid"
    UNSAFE = "unsafe"
    SAFE = "safe"
    VALID = "valid"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"