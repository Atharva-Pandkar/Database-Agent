# New Implementation
from typing import Tuple, Dict, Any
from app.core.logger import logger
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

from app.schemas.state import AgentState, ExecutionStatus
from app.workflows.base import BaseNode
from app.services.csv_operations import CSVOperations
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from pathlib import Path
load_dotenv()

class LLM:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    def get_llm_response(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        return response.choices[0].message.content

class QueryGenerator(BaseNode):
    csv_ops = CSVOperations(str(Path("data") / "sales_and_rating_cleaned.csv"))
    llm = LLM()
    
    system_prompt = """
    You are an expert at generating search parameters for a gaming dataset. 
    Based on the user's query, generate a JSON object with search parameters.

   Column names:
   "Title", "Console", "Developer", "Publisher", "Release Date", "Critic Score", 
   "User Score", "Total Sales", "Japan Sales", "NA Sales", "PAL Sales", 
   "Other Sales", "Last Update", "Total Shipped", "VGChartz Score"

    Some Exceptional Cases:
    - Last Update is in format "DDth MMM YY" (e.g., "29th Feb 00", "3rd Sep 97")
    - every sales column is in format "5.2m" but also NaN values

CRITICAL SECURITY RULES:
1. ONLY use pandas operations and basic Python functions
2. NEVER use eval(), exec(), __import__(), open(), or any file operations
3. NEVER import os, sys, subprocess, or other system modules
4. ONLY work with the provided DataFrame 'df'
5. Always assign final result to variable 'result'
6. Handle edge cases and potential errors
7. Be efficient with memory and performance
8. Use vectorized operations when possible
9. Handle exceptional cases accordingly


Generate ONLY the pandas code, no explanations.
There should be no markdown formatting.
There should be no backticks or quotes around the code.

    """
    
    @staticmethod
    async def process(state: AgentState, config: RunnableConfig) -> AgentState:
        """Generate search parameters based on the query."""
        prompt = f"""
        Generate pandas code to search/filter the DataFrame 'df' based on this query: "{state.task_graph.query}"
Additional parameters: {state.current_task.task_node.parameters}
Requirements:
1. Use pandas operations to filter the DataFrame
2. Handle text searches with case-insensitive matching where appropriate
3. Support multiple column searches
5. Assign the final result to a variable named 'result'
7. Handle missing values appropriately
1. Use pandas aggregation functions (sum, mean, count, etc.)
2. Handle groupby operations if needed
6. Format numbers appropriately
7. Handle exceptional cases accordingly
Genrate only the pandas code, no explanations.
        """
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {"role": "system", "content": QueryGenerator.system_prompt},
                {"role": "user", "content": prompt}
            ],
        )
        
        # Extract and clean the code
        code = response.choices[0].message.content
        print(code)
        # Remove any markdown formatting
        if code.startswith('```json'):
            code = code[8:]
        elif code.startswith('```python'):
            code = code[10:]
        elif code.startswith('```'):
            code = code[3:]
        if code.endswith('```'):
            code = code[:-3]
        
        # Clean up any extra whitespace or newlines
        code = code.strip()
        
        logger.info(f"Generated code: {code}", "db_search/generate")
        state.current_task.result = code
        return state

class Executor(BaseNode):
    csv_ops = CSVOperations(str(Path("data") / "sales_and_rating_cleaned.csv"))
    
    @staticmethod
    async def process(state: AgentState, config: RunnableConfig) -> AgentState:
        """Execute the search using CSVOperations."""
        try:
            logger.info(
                f"Executing search with parameters: {state.current_task.result}",
                "db_search/executor"
            )
            
            # Execute the pandas code directly
            result = Executor.csv_ops.search(state.current_task.result)
            
            logger.info(
                f"Search executed successfully: {result}",
                "db_search/executor"
            )
            
            if state.current_task:
                state.current_task.status = ExecutionStatus.SUCCESS
                state.completed_tasks[state.current_task.task_node.id] = state.current_task
                state.current_task.result = result
                state.db_search_used = True
                state.collected_evidence.append({
                    "db_search for " + state.task_graph.query: str(result)
                })
                state.current_task = None
            
        except Exception as e:
            logger.error(f"Error executing search: {e}", "db_search/executor")
            state.current_task.status = ExecutionStatus.FAILED
            state.current_task.error = str(e)
            state.current_task = None
            return state
        
        return state

def create_db_search_graph() -> StateGraph:
    """Creates the DB search subgraph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("generate", QueryGenerator.process)
    workflow.add_node("execute", Executor.process)
    
    # Add edges
    workflow.add_edge("generate", "execute")
    
    # Set entry point
    workflow.set_entry_point("generate")
    
    graph = workflow.compile()
    return graph

# Old Implementation (Commented Out)
# """
# from typing import Tuple
# from app.core.logger import logger
# from langchain_core.runnables import RunnableConfig
# from langgraph.graph import StateGraph

# from app.schemas.state import AgentState, ExecutionStatus
# from app.workflows.base import BaseNode
# from app.services.db_service import DBService
# from openai import OpenAI
# from dotenv import load_dotenv
# import os
# load_dotenv()

# class LLM:
#     def __init__(self):
#         self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#     def get_llm_response(self, prompt: str) -> str:
#         response = self.client.chat.completions.create(
#             model="gpt-4o-mini",
#             temperature=0.1,
#             messages=[
#                 {"role": "system", "content": prompt}
#             ]
#         )
#         return response.choices[0].message.content

# class QueryGenerator(BaseNode):
#     db_service = DBService()
#     llm = LLM()
    
#     system_prompt = \"""
#     You are an expert pandas developer. Generate secure, efficient pandas code based on the user's requirements.

# CRITICAL SECURITY RULES:
# 1. ONLY use pandas operations and basic Python functions
# 2. NEVER use eval(), exec(), __import__(), open(), or any file operations
# 3. NEVER import os, sys, subprocess, or other system modules
# 4. ONLY work with the provided DataFrame 'df'
# 5. Always assign final result to variable 'result'
# 6. Handle edge cases and potential errors
# 7. Be efficient with memory and performance
# 8. Use vectorized operations when possible

# CRITICAL DATA TYPE & NaN HANDLING:
# - Always check the data types in the schema before using string methods
# - If a column is numeric (int64, float64), do NOT use .str accessor
# - If a column is object/string, you can use .str accessor BUT handle NaN first
# - NEVER use .str accessor directly on columns with NaN values
# - Always use .fillna('') or .dropna() before .str operations
# - Sales columns contain strings like "5.2m" but also NaN values
# - Example: df['col'].fillna('').str.replace('m', '') not df['col'].str.replace('m', '')
# - Use pd.to_numeric() after cleaning string values
# - Always handle missing values (NaN) appropriately in operations

# CRITICAL DATE HANDLING:
# - Dates are in format "DDth MMM YY" (e.g., "29th Feb 00", "3rd Sep 97")
# - For date comparisons:
#   1. First clean the date string:
#      df["Release Date"].fillna('').str.extract(r'(\d+)[a-z]{2}\s+(\w+)\s+(\d+)')
#   2. Then use pd.to_datetime with custom format:
#      pd.to_datetime(cleaned_date, format='%d %b %y', errors='coerce')
# - Always handle 'N/A' values in dates before operations
# - For date ranges, convert both dates to datetime for comparison
# - Example date handling:
#   def parse_custom_date(date_str):
#       if pd.isna(date_str) or date_str == 'N/A':
#           return pd.NaT
#       return pd.to_datetime(date_str.replace('st','').replace('nd','').replace('rd','').replace('th',''), format='%d %b %y')
#   df["Release Date"] = df["Release Date"].apply(parse_custom_date)

# Generate ONLY the pandas code, no explanations.
#     \"""
#     generator_prompt = \"""
#         You are a helpful SQL Query Generator, 
#         You will be given a user description of what they want to do with the database. 
#         You will need to generate a SQL query to do that.

#         The table name is 'games' and it has the following columns (MUST be quoted in queries):
#         "Title", "Console", "Developer", "Publisher", "Release Date", "Critic Score", 
#         "User Score", "Total Sales", "Japan Sales", "NA Sales", "PAL Sales", 
#         "Other Sales", "Last Update", "Total Shipped", "VGChartz Score"
        
#         Sample Data: ( IN CSV FORMAT)
#         PS,9.5,Polyphony Digital,Gran Turismo,N/A,N/A,N/A,N/A,N/A,Sony Computer Entertainment,30th Apr 98,N/A,10.85m,N/A,N/A
#         PS,9.6,SquareSoft,Final Fantasy VII,N/A,23rd Mar 19,N/A,N/A,N/A,Sony Computer Entertainment,03rd Sep 97,N/A,9.90m,9.5,N/A
#         PS,9.2,Polyphony Digital,Gran Turismo 2,N/A,N/A,N/A,N/A,N/A,Sony Computer Entertainment,17th Jan 99,N/A,9.37m,N/A,N/A
#         PS,9.4,SquareSoft,Final Fantasy VIII,N/A,N/A,N/A,N/A,N/A,Square EA,07th Sep 99,N/A,8.60m,N/A,N/A

#         IMPORTANT:
#         1. Use only the table name 'games'
#         2. Return ONLY the SQL query, no markdown, no explanations
#         3. All data is stored in VARCHAR format, for calculations use CAST(column_name AS Data_Type) for mathematical operations
#         4. Make sure column names match exactly (case sensitive)
#         5. Column may containe NULL("N/A") values, handle them accordingly
#         6. Some company names may be abbrivated, like "EA" for Electronic Arts, use LIKE operator to find them and try using full name.
#         5. Do not use backticks or quotes around the query
#         6. Use the parameters provided to you to generate the query
#         7. Use the column names provided to you to generate the query
#         8. Use the table name provided to you to generate the query
        
#         Example Queries:
#         SELECT AVG(
#        TRY_CAST(
#            NULLIF("Critic Score", 'N/A')
#            AS DECIMAL
#        )
#    )
#    Generate a query to do the following:
#         {user_description}
        
#         Parameters to consider:
#         {parameters}
#         \"""
#     pandas_genrate_prompt = \"""
    
#     Generate pandas code to search/filter compute/aggregate the DataFrame 'df' based on this query: "{user_description}"

#         Column names:
#         "Title", "Console", "Developer", "Publisher", "Release Date", "Critic Score", 
#         "User Score", "Total Sales", "Japan Sales", "NA Sales", "PAL Sales", 
#         "Other Sales", "Last Update", "Total Shipped", "VGChartz Score"
        
#         Sample Data: ( IN CSV FORMAT)
#         PS,9.5,Polyphony Digital,Gran Turismo,N/A,N/A,N/A,N/A,N/A,Sony Computer Entertainment,30th Apr 98,N/A,10.85m,N/A,N/A
#         PS,9.6,SquareSoft,Final Fantasy VII,N/A,23rd Mar 19,N/A,N/A,N/A,Sony Computer Entertainment,03rd Sep 97,N/A,9.90m,9.5,N/A
#         PS,9.2,Polyphony Digital,Gran Turismo 2,N/A,N/A,N/A,N/A,N/A,Sony Computer Entertainment,17th Jan 99,N/A,9.37m,N/A,N/A
#         PS,9.4,SquareSoft,Final Fantasy VIII,N/A,N/A,N/A,N/A,N/A,Square EA,07th Sep 99,N/A,8.60m,N/A,N/A

# Requirements:
# 1. Use pandas operations to filter the DataFrame
# 2. Handle text searches with case-insensitive matching where appropriate
# 3. Support multiple column searches
# 4. Return a subset of the DataFrame
# 5. Assign the final result to variable named 'result'
# 7. Handle missing values appropriately
# 8. Use pandas aggregation functions (sum, mean, count, etc.)
# 9. Handle groupby operations if needed
# 10. Return computed values as appropriate data structure

# ADDITIONAL PARAMETERS:
# {parameters}

# Only return the pandas code, no markdown, no explanations
# Do not add any backticks or quotes around the code

#     \"""    
#     @staticmethod
#     async def process(state: AgentState, config: RunnableConfig) -> AgentState:
#         """Generate database query based on task parameters."""
#         prompt_user = QueryGenerator.pandas_genrate_prompt.format(
#             user_description=state.task_graph.query, 
#             parameters=state.current_task.task_node.parameters

#         )
#         client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             temperature=0.1,
#             messages=[
#                 {"role": "system", "content": QueryGenerator.system_prompt},
#                 {"role": "user", "content": prompt_user}
#             ]
#         )
#         response = response.choices[0].message.content
#         state.current_task.result = response
#         return state

# class QueryValidator(BaseNode):
#     validator_prompt = \"""
#         You are a helpful SQL Query Validator, 
#         You will be given a SQL query and a user description of what they want to do with the database.
#         You will need to validate the query to make sure it does what the user wants.
#         Return EXACTLY "TRUE" if the query is valid, or "FALSE" if it's not.
        
#         Query:
#         {query}
        
#         User Description:
#         {user_description}
#         \"""
#     @staticmethod
#     async def process(state: AgentState, config: RunnableConfig) -> AgentState:
#         """Validate the generated query."""
#         prompt = QueryValidator.validator_prompt.format(query=state.current_task.result, user_description=state.task_graph.query)
#         response = universal_llm.get_llm_response(prompt)
        
#         if response.strip().upper() == "TRUE":
#             state.current_task.result["validated"] = True
#             return state
#         else:
#             state.current_task.status = ExecutionStatus.RETRY
#             state.current_task.result = "False"
#             state.current_task.retry_count += 1
#             return state

# class Executor(BaseNode):
#     db_service = DBService()
    
#     @staticmethod
#     async def process(state: AgentState, config: RunnableConfig) -> AgentState:
#         """Execute the validated query."""
#         try:
#             logger.info(f"Executing query: {state.current_task.result}","db_search/executor")
#             result =await Executor.db_service.execute_pandas_query(state.current_task.result)
#             logger.info(f"Query executed successfully: {result}","db_search/executor")
#         except Exception as e:
#             logger.error(f"Error executing query: {e}","db_search/executor")
#             state.current_task.status = ExecutionStatus.FAILED
#             state.current_task.result = str(e)
#             return  state
        
#         if state.current_task:
#             state.current_task.status = ExecutionStatus.SUCCESS
#             state.completed_tasks[state.current_task.task_node.id] = state.current_task
#             state.current_task.result = result
#             state.db_search_used = True
#             state.collected_evidence.append({"db_search for " + state.task_graph.query  :   str(result)})
#             state.current_task = None
        
#         return  state

# def create_db_search_graph() -> StateGraph:
#     """Creates the DB search subgraph."""
#     workflow = StateGraph(AgentState)
    
#     # Add nodes
#     workflow.add_node("generate", QueryGenerator.process)
#     # workflow.add_node("validate", QueryValidator.process)
#     workflow.add_node("execute", Executor.process)
    
#     # Add edges
#     # workflow.add_edge("generate", "validate")
#     # workflow.add_conditional_edges("validate",validation_result, {
#     #     "True": "execute",
#     #     "False": "generate"
#     # })
#     workflow.add_edge("generate", "execute")
    
#     # Set entry point
#     workflow.set_entry_point("generate")
    
#     graph = workflow.compile()
#     return graph

# def validation_result(state: AgentState) -> str:
#     if state.current_task.result == "False":
#         return "False"
#     else:
#         return "True"

# universal_llm = LLM()
# """