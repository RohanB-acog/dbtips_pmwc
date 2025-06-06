"""A tool for running python code in a REPL."""

import ast
import asyncio
import re
import sys
from contextlib import redirect_stdout
from io import StringIO
from typing import Any, Dict, Optional, Type
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.pydantic_v1 import BaseModel, Field, root_validator
from langchain.tools.base import BaseTool

from langchain_experimental.utilities.python import PythonREPL

from intelligent_interpreter import intelligent_interpreter






def _get_default_python_repl() -> PythonREPL:
    return PythonREPL(_globals=globals(), _locals=None)


def sanitize_input(query: str) -> str:
    """Sanitize input to the python REPL.
    Remove whitespace, backtick & python (if llm mistakes python console as terminal)

    Args:
        query: The query to sanitize

    Returns:
        str: The sanitized query
    """

    # Removes `, whitespace & python from start
    query = re.sub(r"^(\s|`)*(?i:python)?\s*", "", query)
    # Removes whitespace & ` from end
    query = re.sub(r"(\s|`)*$", "", query)
    return query


class PythonREPLTool(BaseTool):
    """A tool for running python code in a REPL."""

    name: str = "Python_REPL"
    description: str = (
        "A Python shell. Use this to execute python commands. "
        "Input should be a valid python command. "
        "If you want to see the output of a value, you should print it out "
        "with `print(...)`."
    )
    python_repl: PythonREPL = Field(default_factory=_get_default_python_repl)
    sanitize_input: bool = True

    def _run(
            self,
            query: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Any:
        """Use the tool."""
        if self.sanitize_input:
            query = sanitize_input(query)
        return self.python_repl.run(query)

    async def _arun(
            self,
            query: str,
            run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Any:
        """Use the tool asynchronously."""
        if self.sanitize_input:
            query = sanitize_input(query)

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self.run, query)

        return result


class PythonInputs(BaseModel):
    query: str = Field(description="code snippet to run")



class PythonAstREPLTool(BaseTool):
    """A tool for running python code in a REPL."""

    name: str = "python_repl_ast"
    description: str = (
        "A Python shell. Use this to execute python commands. "
        "Input should be a valid python command. "
        "When using this tool, sometimes output is abbreviated - "
        "make sure it does not look abbreviated before using it in your answer."
    )
    globals: Optional[Dict] = Field(default_factory=dict)
    locals: Optional[Dict] = Field(default_factory=dict)
    sanitize_input: bool = True
    args_schema: Type[BaseModel] = PythonInputs

    @root_validator(pre=True, allow_reuse=True)
    def validate_python_version(cls, values: Dict) -> Dict:
        """Validate valid python version."""
        if sys.version_info < (3, 9):
            raise ValueError(
                "This tool relies on Python 3.9 or higher "
                "(as it uses new functionality in the `ast` module, "
                f"you have Python version: {sys.version}"
            )
        return values

    def _run(
            self,
            query: str,
            run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        logger.info(f"PythonAstREPLTool _run called with query##############################: {query}")
        try:
            if self.sanitize_input:
                query = sanitize_input(query)
            tree = ast.parse(query)
            module = ast.Module(tree.body[:-1], type_ignores=[])
            exec(ast.unparse(module), self.globals, self.locals)  # type: ignore
            module_end = ast.Module(tree.body[-1:], type_ignores=[])
            module_end_str = ast.unparse(module_end)  # type: ignore
            io_buffer = StringIO()
            try:
                with redirect_stdout(io_buffer):
                    ret = eval(module_end_str, self.globals, self.locals)
                    if ret is None:
                        output = io_buffer.getvalue()
                        if "Error" in str(output):
                            intelligent_output = intelligent_interpreter("gpt-3.5-turbo", query, output)
                            output = output + "\n" + intelligent_output
                        if "SyntaxError" in str(output):
                            output = output + " " + "Action Input should be a valid python code."
                        if len(str(output)) == 0:
                            output = "Code executed successfully"
                        # Calculate the number of tokens using tiktokens
                        # encoding = tiktoken.get_encoding("cl100k_base") # From openai cookbook #https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
                        # num_tokens = len(encoding.encode(str(output)))
                        # if num_tokens > 100:
                        #     output = """The length of the output of your Action Input is too long. All the values are stored in the variables that you declared in your Action Input and are available. Take the next step as specified in the output format(Thought, Action, Action Input and Final Answer)"""
                        return output
                    else:
                        output = ret
                        if "Error" in str(output):
                            intelligent_output = intelligent_interpreter("gpt-3.5-turbo", query, output)
                            output = output + "\n" + intelligent_output
                        if "SyntaxError" in str(output):
                            output = output + " " + "Action Input should be a valid python code."
                        if len(str(output)) == 0:
                            output = "Code executed successfully."
                        # Calculate the number of tokens using tiktokens
                        # encoding = tiktoken.get_encoding("cl100k_base") # From openai cookbook #https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
                        # num_tokens = len(encoding.encode(str(output)))
                        # if num_tokens > 100:
                        #     output = """The length of the output of your Action Input is too long. All the values are stored in the variables that you declared in your Action Input and are available. Take the next step as specified in the output format(Thought, Action, Action Input and Final Answer)"""
                        return output
            except Exception:
                with redirect_stdout(io_buffer):
                    exec(module_end_str, self.globals, self.locals)
                    output = io_buffer.getvalue()
                    if "Error" in str(output):
                        intelligent_output = intelligent_interpreter("gpt-3.5-turbo", query, output)
                        output = output + "\n" + intelligent_output
                    if "SyntaxError" in str(output):
                        output = output + " " + "Action Input should be a valid python code."
                    if len(str(output)) == 0:
                        output = "Code executed successfully."
                    # Calculate the number of tokens using tiktokens
                    # encoding = tiktoken.get_encoding("cl100k_base") # From openai cookbook #https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
                    # num_tokens = len(encoding.encode(str(output)))
                    # if num_tokens > 100:
                    #     output = """The length of the output of your Action Input is too long. All the values are stored in the variables that you declared in your Action Input and are available. Take the next step as specified in the output format(Thought, Action, Action Input and Final Answer)"""
                return output
        except Exception as e:
            output = "{}: {}".format(type(e).__name__, str(e))
            if "Error" in str(output):
                intelligent_output = intelligent_interpreter("gpt-3.5-turbo", query, output)
                output = output + "\n" + intelligent_output
            if "SyntaxError" in str(output):
                output = output + " " + "Action Input should be a valid python code."
            if len(str(output)) == 0:
                output = "Code executed successfully"
            # Calculate the number of tokens using tiktokens
            # encoding = tiktoken.get_encoding("cl100k_base") # From openai cookbook #https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
            # num_tokens = len(encoding.encode(str(output)))
            # if num_tokens > 1000:
            #     output = """The length of the output of your Action Input is too long. All the values are stored in the variables that you declared in your Action Input and are available. Take the next step as specified in the output format(Thought, Action, Action Input and Final Answer)"""
            return output

    async def _arun(
            self,
            query: str,
            run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Any:
        """Use the tool asynchronously."""
        logger.info(f"PythonAstREPLTool _run called with query##############################2: {query}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._run, query)

        return result