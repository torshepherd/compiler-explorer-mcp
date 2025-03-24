from typing import Any, TypeVar
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP, Context
import httpx
import json
from fastapi import HTTPException
import re

T = TypeVar("T")


class CompilationFilters(BaseModel):
    """Configuration for filtering compiler output.

    Attributes:
        binary: Include binary output in the response (default: False)
        binary_object: Include binary object output (default: False)
        comment_only: Include only comments from the output (default: True)
        demangle: Demangle C++ symbols in the output (default: True)
        directives: Include compiler directives in the output (default: True)
        execute: Include execution results (default: False)
        intel: Use Intel syntax for assembly output (default: True)
        labels: Include labels in the output (default: True)
        library_code: Include library code in the output (default: False)
        trim: Trim whitespace from the output (default: False)
    """

    binary: bool = False
    binary_object: bool = False
    comment_only: bool = True
    demangle: bool = True
    directives: bool = True
    execute: bool = False
    intel: bool = True
    labels: bool = True
    library_code: bool = False
    trim: bool = False


class Library(BaseModel):
    """Represents a library dependency for compilation.

    Attributes:
        id: Unique identifier for the library (e.g., 'boost', 'fmt')
        version: Version string of the library (e.g., '1.76.0')
    """

    id: str
    version: str


class CompilerExplorerError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CompilerExplorerClient:
    """Client for interacting with Compiler Explorer API.

    This client provides methods to interact with the Compiler Explorer API,
    handling authentication, request formatting, and error handling.

    Args:
        base_url: Base URL for the Compiler Explorer API (default: "https://godbolt.org/api")
    """

    def __init__(self, base_url: str = "https://godbolt.org/api"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30.0,
        )

    async def _make_request(self, method: str, url: str, **kwargs) -> Any:
        """Make HTTP request with error handling.

        Args:
            method: HTTP method to use (GET, POST, etc.)
            url: URL to make the request to
            **kwargs: Additional arguments to pass to the request

        Returns:
            Parsed JSON response from the API

        Raises:
            CompilerExplorerError: If the request fails or returns invalid JSON
        """
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()

            # Ensure we have valid JSON response
            try:
                return response.json()
            except json.JSONDecodeError as e:
                print(f"Response content: {response.text}")  # Debug log
                raise CompilerExplorerError(f"Invalid JSON response: {str(e)}")

        except httpx.TimeoutException:
            raise CompilerExplorerError("Request timed out")
        except httpx.HTTPStatusError as e:
            raise CompilerExplorerError(
                f"HTTP error occurred: {str(e)}", status_code=e.response.status_code
            )
        except Exception as e:
            raise CompilerExplorerError(f"Unexpected error: {str(e)}")

    async def list_languages(self) -> list[dict[str, str]]:
        """Get list of supported programming languages.

        Returns:
            List of dictionaries containing language information, each with keys:
            - id: Unique identifier for the language
            - name: Display name of the language
            - extensions: List of file extensions associated with the language

        Raises:
            CompilerExplorerError: If the API request fails
        """
        return await self._make_request("GET", f"{self.base_url}/languages")

    async def list_compilers(self, language: str | None = None) -> list[dict[str, str]]:
        """Get list of available compilers.

        Args:
            language: Optional language filter to get compilers for a specific language

        Returns:
            List of dictionaries containing compiler information, each with keys:
            - id: Unique identifier for the compiler
            - name: Display name of the compiler
            - semver: Version string of the compiler
            - language: Programming language the compiler supports

        Raises:
            CompilerExplorerError: If the API request fails
        """
        url = f"{self.base_url}/compilers"
        if language:
            url += f"/{language}"
        return await self._make_request("GET", url)

    async def compile_code(
        self,
        source: str,
        compiler: str,
        options: str = "",
        filters: CompilationFilters = CompilationFilters(),
        libraries: list[Library] = [],
    ) -> dict:
        """Compile code using specified compiler.

        Args:
            source: Source code to compile
            compiler: Compiler ID to use (e.g., 'gcc-12.2')
            options: Optional compiler flags and options
            filters: Optional configuration for filtering compiler output
            libraries: Optional list of library dependencies

        Returns:
            Dictionary containing compilation results with keys:
            - code: Exit code of the compilation
            - stdout: Standard output from the compiler
            - stderr: Standard error from the compiler
            - asm: Generated assembly (if applicable)

        Raises:
            CompilerExplorerError: If compilation fails or API request fails
        """
        data = {
            "source": source,
            "options": {
                "userArguments": options or "",
                "filters": filters.dict() if filters else CompilationFilters().dict(),
                "libraries": [lib.dict() for lib in libraries] if libraries else [],
            },
        }
        return await self._make_request(
            "POST", f"{self.base_url}/compiler/{compiler}/compile", json=data
        )

    async def get_opcode_documentation(self, instruction_set: str, opcode: str) -> dict:
        """Get documentation for a specific opcode in a given instruction set.

        Args:
            instruction_set: Instruction set to search for opcode documentation
            opcode: Opcode to search for documentation
        """
        return await self._make_request(
            "GET", f"{self.base_url}/asm/{instruction_set}/{opcode}"
        )


def get_unversioned_compiler_name(compiler_name: str, semver: str) -> str:
    """Get the unversioned compiler name from the versioned name.

    Args:
        compiler_name: Full compiler name including version
        semver: Version string to remove

    Returns:
        Cleaned compiler name without version information

    Example:
        >>> get_unversioned_compiler_name("gcc-12.2", "12.2")
        "gcc"
    """
    return (
        compiler_name.replace(semver, "").replace("none", "").replace("()", "").strip()
    )


def infer_compiler_id(
    compiler_name_or_id: str, compilers: list[dict[str, str]]
) -> str | None:
    """Infer the compiler ID from a name or ID string.

    Args:
        compiler_name_or_id: Either a compiler ID or name to match
        compilers: List of available compilers from the API

    Returns:
        Matching compiler ID if found, None otherwise

    Example:
        >>> compilers = [{"id": "gcc-12.2", "name": "GCC 12.2"}]
        >>> infer_compiler_id("gcc", compilers)
        "gcc-12.2"
    """
    if compiler_name_or_id in [c["id"] for c in compilers]:
        compiler_id = compiler_name_or_id
    else:
        # Get the compiler ID from the name
        compiler_id = next(
            (
                c["id"]
                for c in compilers
                if c["name"].lower().strip() == compiler_name_or_id.lower().strip()
            ),
            None,
        )
    return compiler_id


# Create an MCP server
mcp = FastMCP("Compiler Explorer Bridge")
ce_client = CompilerExplorerClient()


@mcp.tool()
async def list_languages() -> list[dict[str, str]]:
    """Get a list of supported programming languages.

    Returns:
        List of dictionaries containing language information, each with keys:
        - id: Unique identifier for the language
        - name: Display name of the language
        - extensions: List of file extensions associated with the language

    Raises:
        HTTPException: If the API request fails
    """
    try:
        return await ce_client.list_languages()
    except CompilerExplorerError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


# @mcp.tool()
# async def list_compilers() -> List[str]:
#     """Get available compilers for a language"""
#     try:
#         compilers = await ce_client.list_compilers()
#         return list(
#             {get_unversioned_compiler_name(c["name"], c["semver"]) for c in compilers}
#         )
#     except CompilerExplorerError as e:
#         raise HTTPException(status_code=e.status_code, detail=str(e))


@mcp.tool()
async def list_compilers_for_language(language: str) -> list[str]:
    """Get available compilers for a specific programming language.

    Args:
        language: Programming language to get compilers for (e.g., 'cpp', 'rust')

    Returns:
        List of unversioned compiler names available for the language

    Raises:
        HTTPException: If the API request fails

    Example:
        >>> await list_compilers_for_language("cpp")
        ["gcc", "clang", "msvc"]
    """
    try:
        compilers = await ce_client.list_compilers(language)
        return list(
            {get_unversioned_compiler_name(c["name"], c["semver"]) for c in compilers}
        )
    except CompilerExplorerError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@mcp.tool()
async def list_compiler_versions(compiler_regex: str) -> list[dict[str, str]]:
    """Get available compiler versions matching a compiler name regex.

    NOTE: This may return a lot of results! Choose a specific regex to narrow down the results and not overflow the MCP client.

    Args:
        compiler_regex: Regular expression to match compiler names (case-insensitive)

    Returns:
        List of dictionaries containing matching compiler information, each with keys:
        - id: Unique identifier for the compiler
        - name: Display name of the compiler
        - semver: Version string of the compiler

    Raises:
        HTTPException: If the API request fails

    Example:
        >>> await list_compiler_versions("gcc")
        [{"id": "gcc-12.2", "name": "GCC 12.2"}, {"id": "gcc-11.3", "name": "GCC 11.3"}]

        >>> await list_compiler_versions("clang.*trunk")
        [..., {"id": "irclangtrunk", "name": "clang (trunk)", "lang": "llvm", "compilerType": "", "semver": "(trunk)", "instructionSet": "amd64"}, ...]
    """
    compilers = await ce_client.list_compilers()
    return [
        c
        for c in compilers
        if re.search(compiler_regex, c["name"], re.IGNORECASE)
        or re.search(compiler_regex, c["id"], re.IGNORECASE)
    ]


@mcp.tool()
async def compile_code(
    source: str,
    language: str,
    compiler: str,
    ctx: Context,
    options: str = "",
    filters: CompilationFilters = CompilationFilters(),
    libraries: list[Library] = [],
) -> dict:
    """Compile source code using specified compiler and options.

    Args:
        source: Source code to compile
        language: Programming language of the source code
        compiler: Compiler name or ID to use
        ctx: MCP context for logging and error reporting
        options: Compiler flags and options
        filters: Configuration for filtering compiler output
        libraries: List of library dependencies

    Returns:
        Dictionary containing compilation results with keys:
        - code: Exit code of the compilation
        - stdout: Standard output from the compiler
        - stderr: Standard error from the compiler
        - asm: Generated assembly (if applicable)

    Raises:
        HTTPException: If compilation fails, compiler not found, or API request fails

    Example:
        >>> result = await compile_code(
        ...     source="int main() { return 0; }",
        ...     language="cpp",
        ...     compiler="gcc",
        ...     ctx=ctx
        ... )
    """
    try:
        compilers = await ce_client.list_compilers(language)
        compiler_id = infer_compiler_id(compiler, compilers)
        if not compiler_id:
            await ctx.error(
                message=f"Compiler '{compiler}' not found",
                level="error",
            )
            raise HTTPException(
                status_code=404, detail=f"Compiler '{compiler}' not found"
            )
        await ctx.log(
            message=f"Inferred compiler {compiler_id} from {compiler}. Compiling...",
            level="info",
        )
        return await ce_client.compile_code(
            source=source,
            compiler=compiler_id,
            options=options,
            filters=filters,
            libraries=libraries,
        )
    except CompilerExplorerError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@mcp.tool()
async def get_opcode_documentation(instruction_set: str, opcode: str) -> dict[str, str]:
    """Get documentation for a specific opcode in a given instruction set.
    If a user asks about an opcode, but you don't have the instruction set, you can query list_compiler_versions for a specific compiler and it will tell you the instruction set.
    You are not an expert on opcodes, so if a user asks about an opcode, you should always use this tool!

    Args:
        instruction_set: Instruction set to search for opcode documentation
        opcode: Opcode to search for documentation

    Example:
        >>> await get_opcode_documentation("amd64", "lea")

    """
    resp = await ce_client.get_opcode_documentation(instruction_set, opcode)
    resp.pop("html")
    return resp


if __name__ == "__main__":
    mcp.run()
