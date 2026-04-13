"""
This module is used to store the configurations.
"""

import re

# ─────────────────────────────────────────────
#  Provider definitions
#  Each provider has:
#    - name        : display name
#    - emoji       : used in terminal output
#    - regex_list  : list of (pattern, too_many_results, result_too_long)
# ─────────────────────────────────────────────
PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "emoji": "🤖",
        "regex_list": [
            # Named Project API Key (new format)
            (re.compile(r"sk-proj-[A-Za-z0-9-_]{74}T3BlbkFJ[A-Za-z0-9-_]{73}A"), True, True),
            # Service Account key (new format)
            (re.compile(r"sk-svcacct-[A-Za-z0-9-_]{74}T3BlbkFJ[A-Za-z0-9-_]{73}A"), False, True),
            # Old Project API Key
            (re.compile(r"sk-proj-[A-Za-z0-9-_]{58}T3BlbkFJ[A-Za-z0-9-_]{58}"), True, True),
            # Short project key
            (re.compile(r"sk-proj-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}"), True, False),
        ],
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "emoji": "🧠",
        "regex_list": [
            # Standard Anthropic API key (api03 format, long)
            (re.compile(r"sk-ant-api03-[A-Za-z0-9\-\_]{93}AA"), False, True),
            # Generic Anthropic key fallback
            (re.compile(r"sk-ant-[A-Za-z0-9\-\_]{40,120}"), False, False),
        ],
    },
    "gemini": {
        "name": "Google Gemini",
        "emoji": "💎",
        "regex_list": [
            # Google API key (used by Gemini and other Google services)
            (re.compile(r"AIza[A-Za-z0-9\-\_]{35}"), True, False),
        ],
    },
}

# Backward-compatible alias (OpenAI only)
REGEX_LIST = PROVIDERS["openai"]["regex_list"]

# ─────────────────────────────────────────────
#  Search configuration
# ─────────────────────────────────────────────
KEYWORDS = [
    "CoT", "DPO", "RLHF", "agent", "ai model", "aios", "api key", "apikey",
    "artificial intelligence", "chain of thought", "chatbot", "chatgpt",
    "competitor analysis", "content strategy", "conversational AI",
    "data analysis", "deep learning", "direct preference optimization",
    "experiment", "gpt", "gpt-3", "gpt-4", "gpt4", "key", "keyword clustering",
    "keyword research", "lab", "language model experimentation",
    "large language model", "llama.cpp", "llm", "long-tail keywords",
    "machine learning", "multi-agent", "multi-agent systems",
    "natural language processing", "openai", "personalized AI", "project",
    "rag", "reinforcement learning from human feedback",
    "retrieval-augmented generation", "search intent", "semantic search",
    "thoughts", "virtual assistant", "实验", "密钥", "测试", "语言模型",
    # Extended for new providers
    "anthropic", "claude", "gemini", "google ai", "vertex ai",
]

LANGUAGES = [
    "Dotenv", "Text", "JavaScript", "Python", "TypeScript",
    "Dockerfile", "Markdown", '"Jupyter Notebook"',
    "Shell", "Java", "Go", "C%2B%2B", "PHP",
]

PATHS = [
    "path:.xml OR path:.json OR path:.properties OR path:.sql OR path:.txt OR path:.log OR path:.tmp OR path:.backup OR path:.bak OR path:.enc",
    "path:.yml OR path:.yaml OR path:.toml OR path:.ini OR path:.config OR path:.conf OR path:.cfg OR path:.env OR path:.envrc OR path:.prod",
    "path:.secret OR path:.private OR path:*.key",
]
