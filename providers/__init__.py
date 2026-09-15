from .claude_provider import ClaudeProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .openai_provider import OpenAIProvider
from .grok_provider import GrokProvider

REGISTRY = {
    "claude": ClaudeProvider(),
    "gemini": GeminiProvider(),
    "groq": GroqProvider(),
    "openai": OpenAIProvider(),
    "grok": GrokProvider(),
}
