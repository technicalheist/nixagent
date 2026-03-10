import pytest
from nixagent.memory import ContextWindowManager

def test_no_trim_needed():
    manager = ContextWindowManager(max_messages=10)
    
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "1"},
        {"role": "assistant", "content": "2"},
        {"role": "user", "content": "3"}
    ] # Total 4 messages
    
    trimmed = manager.maybe_trim(messages)
    assert len(trimmed) == 4
    assert trimmed == messages

def test_trim_keeps_system_prompt():
    manager = ContextWindowManager(max_messages=4)
    
    messages = [
        {"role": "system", "content": "System prompt"}, # Index 0
        {"role": "user", "content": "1"},              # Expected to evict
        {"role": "assistant", "content": "2"},         # Expected to evict
        {"role": "user", "content": "3"},              # Keep
        {"role": "assistant", "content": "4"},         # Keep
        {"role": "user", "content": "5"}               # Keep (Total 3 kept + system = 4 -> Oops wait. 6 msgs total minus system = 5. Max allowed is 4. Evicts 1 message? No, logic checks total.)
    ]
    
    # Total messages: 6. max_messages = 4. Needs to evict 6 - 4 = 2 messages.
    # Evicted will be msgs at list indices 0 and 1. (But wait, maybe_trim acts on the whole list including system unless it separates it, let's test.)
    # The actual implementation separates system, then total = len(conversation).
    # Wait, the implementation says `total = len(conversation)` which EXCLUDES the system prompt if present!
    # Let's verify actual behaviour: 
    trimmed = manager.maybe_trim(messages)
    
    assert trimmed[0]["role"] == "system"
    assert trimmed[0]["content"] == "System prompt"
    # System + 4 conversation msgs = 5 total
    assert len(trimmed) == 5
    assert trimmed[1]["content"] == "2" # It evicted "1"
    assert trimmed[-1]["content"] == "5"

def test_summarization():
    def mock_summarizer(evicted_msgs):
        return f"Summarized {len(evicted_msgs)} messages."
        
    manager = ContextWindowManager(max_messages=4, summarizer=mock_summarizer)
    
    messages = [
        {"role": "system", "content": "System"},
        {"role": "user", "content": "1"},
        {"role": "assistant", "content": "2"},
        {"role": "user", "content": "3"},
        {"role": "assistant", "content": "4"},
        {"role": "user", "content": "5"},
        {"role": "assistant", "content": "6"}
    ]
    
    # conversation has 6 msgs. max is 4. Evicts 2.
    trimmed = manager.maybe_trim(messages)
    
    assert len(trimmed) == 6 # System + Summary + 4 kept messages
    assert trimmed[0]["role"] == "system"
    assert "Summarized 2 messages" in trimmed[1]["content"]
    assert trimmed[-4]["content"] == "3"
    assert trimmed[-1]["content"] == "6"
