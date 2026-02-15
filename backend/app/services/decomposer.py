import json
import uuid
from typing import List, Dict, Any
import openai
from ..core.config import get_settings
from ..schemas.decomposer import TaskNode, TaskGraph
from ..schemas.helpers import SubgraphType, ExecutionStatus
from ..core.logger import logger

class DecomposerService:
    def __init__(self):
        self.settings = get_settings()
        self.client = openai.OpenAI(api_key=self.settings.openai_api_key)

    async def decompose_query(self, query: str, context: Dict[str, Any] = None) -> TaskGraph:
        """
        Decompose a user query into a task graph using OpenAI's API.
        """
        # Create system message for task decomposition
        system_message = """You are an expert query decomposer for a gaming dataset analysis system. Your job is to break down natural language queries into executable tasks.

The gaming dataset contains these columns:
- console: Gaming platform (PS1, PS2, PS3, PS4, PS5, PSP, PNP, PSV, etc.)
- critic_score: Professional review scores
- developer: Game development studio
- title: Game title
- japan_sale, na_sales, pal_sales, other_sale: Regional sales figures
- total_sales: Global sales total
- publisher: Game publisher (Square Enix, Ubisoft, Electronic Arts or EA, Capcom, Nintendo, Sony, Microsoft)
- release_date: When game was released
- last_update: When data was last updated
- user_score: User review scores

Available Task Types:
1. db_search: Powerful database operations that can handle complex queries in ONE task
   - Can do: filtering, sorting, ranking, aggregation, top-N results, complex conditions
   - Parameters: {"query": "natural language description", "filters": {"column": [values]}, "limit": number}
      
2. web_search: Search web for missing information
   - Parameters: {"query": "search question as string", "max_results": number, "domains": [optional_list]}
   - Use for: "current gaming trends", "latest PS5 releases", "industry news"

3. db_update: Update database entries with cited sources  


CRITICAL TASK DECOMPOSITION RULES:
 SINGLE TASK examples:
- "Find top 3 PlayStation games with highest ratings" → 1 db_search (not search + compute!)
- "Show average sales for PS5 games" → 1 db_search  
- "List RPG games from 2020-2023 sorted by user score" → 1 db_search

 MULTIPLE TASKS only for different operation types:
- "Find games missing critic scores, research them online, update database" 
  → db_search + web_search + db_update
- "Get top games in PS5 , then analyze their sales trends over time"
  → db_search + web_search

The CSV database can handle complex pandas operations in one call - leverage this power!

Query Intent Patterns:
- web_only: Current gaming news, recent releases, industry trends, anything related to "online search" → web_search only
- db_only_simple: Single database operation (search with filtering/sorting/aggregation)
- db_only_complex: Multi-step database operations requiring intermediate results
- db_web_update: Multi-step workflow: search database → web research → database update

- "Tell me about gaming" → web_only intent, tasks: [web_search]  
- "What is the best PS5 game" → web_only intent, tasks: [web_search] (current info needed)
- Database questions → db_only_simple/complex intents with appropriate tasks

EFFICIENCY PRIORITY: Prefer fewer, smarter tasks over many granular tasks!
Output valid JSON with this structure:
{
  "query_intent": "intent_type",
  "confidence_score": 0.0-1.0,
  "requires_web_search": boolean,
  "requires_db_updates": boolean,
  "tasks": [
    {
      "task_id": "unique_id",
      "task_type": "task_type",
      "description": "what this task does",
      "parameters": {task-specific parameters},
      "depends_on": ["task_ids"],
      "priority": "medium",
    }
  ]
}

Focus on accuracy and create logical task dependencies."""

        # Create user message with query and context
        user_message = f"Query: {query}\n"
        if context:
            user_message += f"Context: {context}\n"

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format={ "type": "json_object" }
            )

            # Parse the response
            result = response.choices[0].message.content
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                logger.error(
                    message="Error parsing JSON response",
                    component="decomposer_service",
                    extras={"response": result}
                )
                # Clean up response if it has markdown formatting
                if result.startswith("```json"):
                    result = result.replace("```json", "").replace("```", "").strip()
                elif result.startswith("```"):
                    result = result.replace("```", "").strip()
                result = json.loads(result)
            parsed_tasks = result.get("tasks", [])

            # Create task nodes
            task_nodes: List[TaskNode] = []
            task_id_map = {}  # Map to store task IDs

            # First pass: Create tasks with IDs
            ids = []
            for task_data in parsed_tasks:
                task_id = str(uuid.uuid4())
                task_id_map[task_data["task_type"]] = task_id
                ids.append(task_id)
                task_node = TaskNode(
                    id=task_id,
                    title=task_data["task_type"],
                    description=task_data["description"],
                    estimated_complexity=task_data.get("estimated_complexity", 1),
                    parameters=task_data.get("parameters", {}),
                    dependencies=task_data.get("dependencies", []),
                    subgraph_type=SubgraphType(task_data["task_type"]),
                    status=ExecutionStatus.PENDING
                )
                task_nodes.append(task_node)
            task_nodes.append(TaskNode(
                id=str(uuid.uuid4()),
                title="conversation",
                description="Respond to the user's query",
                estimated_complexity=1,
                parameters={},
                dependencies=ids,
                subgraph_type=SubgraphType.CONVERSATION,
                status=ExecutionStatus.PENDING
            ))

            # Create and return task graph
            task_graph = TaskGraph(
                id=str(uuid.uuid4()),
                query=query,
                tasks=task_nodes
            )

            logger.info(
                message="Successfully decomposed query into task graph",
                component="decomposer_service",
                extras={
                    "query": query,
                    "task_count": len(task_nodes)
                }
            )

            return task_graph

        except Exception as e:
            logger.error(
                message="Error decomposing query",
                component="decomposer_service",
                extras={
                    "query": query,
                    "error": str(e)
                }
            )
            raise

