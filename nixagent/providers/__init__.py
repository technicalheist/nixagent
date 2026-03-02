from .openai import call_openai
from .anthropic import call_anthropic
from .gemini import call_gemini
from .vertex import call_vertex

__all__ = ["call_openai", "call_anthropic", "call_gemini", "call_vertex"]

def get_provider_caller(provider_name: str):
    provider_lower = provider_name.lower()
    if provider_lower == "anthropic":
        return call_anthropic
    elif provider_lower == "gemini":
        return call_gemini
    elif provider_lower == "vertex":
        return call_vertex
    else:
        return call_openai
