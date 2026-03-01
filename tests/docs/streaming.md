# Test 07: Streaming 

This documentation covers the usage of `tests/test_07_streaming.py`.

## Overview
This test ensures that `Agent.run(..., stream=True)` correctly returns a generator that streams text chunks back without breaking the standard control flow.

## Running the Test
```bash
python tests/test_07_streaming.py
```

## Expected Output
The test initializes an agent and prompts it to write a 3-sentence story. You should see the response progressively appear on the screen in real-time, yielding chunks of the story just like standard LLM chat interfaces.

```text
Running Test 07 - Streaming Response

--- Start Stream ---
[Text will appear here typed out progressively]
--- End Stream ---
```
