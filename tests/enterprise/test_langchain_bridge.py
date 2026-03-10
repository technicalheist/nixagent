import pytest
from nixagent.integrations.langchain_bridge import from_langchain_tool

class MockLangChainTool:
    """Mock representing a LangChain BaseTool implementation."""
    name = "mock_weather"
    description = "Fetches weather."
    
    def run(self, query: str) -> str:
        if query == "London":
            return "Rainy, 15C"
        return "Sunny, 20C"

class MockPydanticTool:
    name = "mock_math"
    description = "Adds two numbers."
    
    # Mocking Pydantic model class
    class MockArgsSchema:
        @classmethod
        def schema(cls):
            return {
                "title": "MathArgs",
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"}
                },
                "required": ["a", "b"]
            }
            
    args_schema = MockArgsSchema
    
    def invoke(self, kwargs: dict) -> str:
        return str(kwargs.get("a", 0) + kwargs.get("b", 0))

def test_from_langchain_basic():
    tool = MockLangChainTool()
    name, fn, schema = from_langchain_tool(tool)
    
    assert name == "mock_weather"
    
    # Ensure fallback schema is generated correctly
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "mock_weather"
    assert "query" in schema["function"]["parameters"]["properties"]
    
    # Ensure callable works and routes correctly to .run()
    assert fn(query="London") == "Rainy, 15C"

def test_from_langchain_pydantic_schema():
    tool = MockPydanticTool()
    name, fn, schema = from_langchain_tool(tool)
    
    assert name == "mock_math"
    
    # Ensure schema is extracted
    params = schema["function"]["parameters"]
    assert "a" in params["properties"]
    assert "b" in params["properties"]
    assert "title" not in params # Should be stripped
    
    # Ensure callable works and routes to .invoke()
    assert fn(a=5, b=3) == "8"

def test_invalid_tool_rejection():
    class NotATool:
        pass
        
    with pytest.raises(TypeError, match="Expected a LangChain BaseTool"):
        from_langchain_tool(NotATool())
