import sys
import os
import requests
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from nixagent.providers.anthropic import call_anthropic
from dotenv import load_dotenv
load_dotenv('.env')

resp = call_anthropic(
    [{"role": "user", "content": "Count from 1 to 5"}], 
    stream=True
)
print("RAW STREAM:")
for line in resp.response.iter_lines():
    print(line)

