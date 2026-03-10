import pytest
import json
from unittest.mock import MagicMock
from nixagent.agent import Agent

def test_structured_output_valid_json():
    # Setup agent with mocked LLM response
    agent = Agent(name="TestAgent", system_prompt="Test")
    
    mock_response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "```json\n{\"summary\": \"Great product\", \"score\": 95}\n```"
            }
        }]
    }
    
    agent._call_llm_with_retry = MagicMock(return_value=mock_response)
    
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "score": {"type": "integer"}
        }
    }
    
    # Run the agent with structured output schema
    result = agent.run("Analyze this review: 'Great product'", output_schema=schema)
    
    # Verify result string was parsed back into a dictionary
    assert isinstance(result, dict)
    assert result["summary"] == "Great product"
    assert result["score"] == 95
    
    # Verify the schema prompt was injected into the messages
    last_user_msg = agent.messages[1]
    assert last_user_msg["role"] == "user"
    assert "IMPORTANT: You must return your final response as a valid JSON object" in last_user_msg["content"]
    assert "summary" in last_user_msg["content"]

def test_structured_output_fallback_on_invalid_json():
    agent = Agent(name="TestAgent", system_prompt="Test")
    
    # Return garbage that isn't JSON
    mock_response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Here is the result: {NOT VALID JSON}"
            }
        }]
    }
    
    agent._call_llm_with_retry = MagicMock(return_value=mock_response)
    
    schema = {"type": "object"}
    
    # Run the agent
    result = agent.run("Do something", output_schema=schema)
    
    # Because JSON parsing fails, it should fallback to returning the raw string
    assert isinstance(result, str)
    assert result == "Here is the result: {NOT VALID JSON}"
