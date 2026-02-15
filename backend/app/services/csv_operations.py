import pandas as pd
import numpy as np
import ast
import re
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from ..core.logger import logger

class CSVOperations:
    def __init__(self, csv_path: str):
        """Initialize with path to CSV file."""
        self.csv_path = Path(csv_path)
        self.df = self._load_csv()
        
        # Security whitelist
        self.allowed_modules = {
            'pandas', 'pd', 'numpy', 'np', 'datetime', 'math', 're'
        }
        self.allowed_functions = {
            'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set',
            'sum', 'min', 'max', 'abs', 'round', 'sorted', 'enumerate',
            'range', 'zip', 'any', 'all'
        }
        
    def _load_csv(self) -> pd.DataFrame:
        """Load CSV file and handle initial data cleaning."""
        try:
            df = pd.read_csv(self.csv_path)
            logger.info(
                message="CSV file loaded successfully",
                component="csv_operations",
                extras={"rows": len(df), "columns": list(df.columns)}
            )
            return df
        except Exception as e:
            logger.error(
                message="Error loading CSV file",
                component="csv_operations",
                extras={"error": str(e)}
            )
            raise

    def _validate_code(self, code: str) -> None:
        """
        Validate generated pandas code for security and syntax.
        
        Args:
            code: Generated pandas code to validate
            
        Raises:
            ValueError: If code fails validation
        """
        try:
            # Parse code into AST for analysis
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in generated code: {str(e)}")
        
        # Security validation
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in ['eval', 'exec', 'compile', '__import__', 'open', 'file']:
                        raise ValueError(f"Dangerous function call detected: {func_name}")
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['system', 'popen', 'subprocess']:
                        raise ValueError(f"Dangerous method call detected: {node.func.attr}")
            
            # Check for dangerous imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.allowed_modules:
                        raise ValueError(f"Disallowed import: {alias.name}")
            
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module not in self.allowed_modules:
                    raise ValueError(f"Disallowed import from: {node.module}")
        
        # Additional string-based checks
        dangerous_patterns = [
            r'__.*__',  # Dunder methods
            r'eval\s*\(',
            r'exec\s*\(',
            r'import\s+os',
            r'import\s+sys',
            r'from\s+os',
            r'from\s+sys'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                raise ValueError(f"Dangerous pattern detected: {pattern}")

    def _execute_pandas_code(self, code: str) -> Any:
        """
        Execute pandas code in a restricted environment.
        
        Args:
            code: Validated pandas code to execute
            
        Returns:
            Result of code execution
        """
        # Create restricted global environment
        safe_globals = {
            '__builtins__': {
                name: func for name, func in __builtins__.items()
                if isinstance(func, type) or name in self.allowed_functions
            } if isinstance(__builtins__, dict) else {
                name: getattr(__builtins__, name) for name in dir(__builtins__)
                if not name.startswith('_') and (
                    isinstance(getattr(__builtins__, name), type) or 
                    name in self.allowed_functions
                )
            },
            'pd': pd,
            'np': np,
            'pandas': pd,
            'numpy': np,
            'df': self.df.copy(),  # Use a copy for safety
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sorted': sorted
        }
        
        try:
            # Execute code with restricted globals
            local_vars = {}
            exec(code, safe_globals, local_vars)
            
            # Return the result (should be stored in 'result' variable)
            if 'result' not in local_vars:
                raise ValueError("Generated code must assign result to 'result' variable")
            
            return local_vars['result']
            
        except Exception as e:
            raise ValueError(f"Code execution failed: {str(e)}\nCode: {code}")

    def search(self, pandas_code: str) -> Any:
        """
        Execute pandas code for searching/querying the DataFrame.
        
        Args:
            pandas_code: String containing pandas code to execute
            
        Returns:
            Query results
        """
        try:
            # Validate the code
            # self._validate_code(pandas_code)
            
            # Execute the code
            result = self._execute_pandas_code(pandas_code)
            
            logger.info(
                message="Search completed successfully",
                component="csv_operations",
                extras={
                    "code": pandas_code,
                    "result_type": type(result).__name__
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                message="Error during search operation",
                component="csv_operations",
                extras={
                    "error": str(e),
                    "code": pandas_code
                }
            )
            raise

    def update(self, pandas_code: str) -> Any:
        """
        Execute pandas code for updating the DataFrame.
        
        Args:
            pandas_code: String containing pandas code to execute
            
        Returns:
            Update results
        """
        try:
            # Validate the code
            self._validate_code(pandas_code)
            
            # Execute the code
            result = self._execute_pandas_code(pandas_code)
            
            # If execution was successful, save the updated DataFrame
            if isinstance(result, pd.DataFrame):
                self.df = result
                self.df.to_csv(self.csv_path, index=False)
            
            logger.info(
                message="Update completed successfully",
                component="csv_operations",
                extras={
                    "code": pandas_code,
                    "result_type": type(result).__name__
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                message="Error during update operation",
                component="csv_operations",
                extras={
                    "error": str(e),
                    "code": pandas_code
                }
            )
            raise

# Example usage:
"""
csv_ops = CSVOperations("path/to/sales_and_rating.csv")

# Search example
search_code = '''
# Filter PS5 games by EA with critic score > 8
result = df[
    (df["Console"] == "PS5") & 
    (df["Publisher"] == "EA") & 
    (df["Critic Score"].fillna(0).astype(float) > 8)
].copy()
'''
result = csv_ops.search(search_code)

# Update example
update_code = '''
# Update critic scores for specific games
mask = df["Title"].str.contains("FIFA", case=False, na=False)
df.loc[mask, "Critic Score"] = 9.0
result = df
'''
result = csv_ops.update(update_code)
"""