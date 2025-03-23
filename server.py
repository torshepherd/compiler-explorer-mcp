from typing import Dict, List, Optional, Any, TypeVar
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
import httpx
import json
from fastapi import HTTPException

T = TypeVar('T')

class CompilationFilters(BaseModel):
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
    id: str
    version: str

class CompilerExplorerError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class CompilerExplorerClient:
    """Client for interacting with Compiler Explorer API"""
    def __init__(self, base_url: str = "https://godbolt.org/api"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def _make_request(self, method: str, url: str, **kwargs) -> Any:
        """Make HTTP request with error handling"""
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
                f"HTTP error occurred: {str(e)}", 
                status_code=e.response.status_code
            )
        except Exception as e:
            raise CompilerExplorerError(f"Unexpected error: {str(e)}")

    async def list_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return await self._make_request("GET", f"{self.base_url}/languages")

    async def list_compilers(self, language: Optional[str] = None) -> List[Dict[str, str]]:
        """Get list of available compilers"""
        url = f"{self.base_url}/compilers"
        if language:
            url += f"/{language}"
        return await self._make_request("GET", url)

    async def compile_code(
        self,
        source: str,
        compiler: str,
        options: Optional[str] = None,
        filters: Optional[CompilationFilters] = None,
        libraries: Optional[List[Library]] = None
    ) -> Dict:
        """Compile code using specified compiler"""
        data = {
            "source": source,
            "options": {
                "userArguments": options or "",
                "filters": filters.dict() if filters else CompilationFilters().dict(),
                "libraries": [lib.dict() for lib in libraries] if libraries else []
            }
        }
        return await self._make_request(
            "POST",
            f"{self.base_url}/compiler/{compiler}/compile",
            json=data
        )

# Create an MCP server
mcp = FastMCP("Compiler Explorer Bridge")
ce_client = CompilerExplorerClient()

@mcp.tool()
async def list_languages() -> List[Dict[str, str]]:
    """Get a list of supported programming languages"""
    try:
        return await ce_client.list_languages()
    except CompilerExplorerError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@mcp.tool()
async def list_compilers(language: Optional[str] = None) -> List[Dict[str, str]]:
    """Get available compilers for a language"""
    try:
        return await ce_client.list_compilers(language)
    except CompilerExplorerError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@mcp.tool()
async def compile_code(
    source: str,
    language: str,
    compiler: str,
    options: Optional[str] = None,
    filters: Optional[CompilationFilters] = None,
    libraries: Optional[List[Library]] = None
) -> Dict:
    """Compile source code using specified compiler and options"""
    try:
        return await ce_client.compile_code(
            source=source,
            compiler=compiler,
            options=options,
            filters=filters,
            libraries=libraries
        )
    except CompilerExplorerError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

if __name__ == "__main__":
    mcp.run()