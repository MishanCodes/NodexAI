"""
Task Analyzer
-------------
Classifies a raw task string into (task_type, difficulty).

Deliberately heuristic/keyword-based rather than an LLM call: this keeps
classification instant, free, and dependency-free, which matters because
it runs before we even know which providers are available. It can be
swapped for an LLM-based classifier later (see README) without touching
any other module — that's the point of keeping it isolated here.
"""
import re

# Creation verbs + an image-ish noun anywhere in the sentence, in either
# order ("create a bird image" / "generate an image of a bird" /
# "draw me a logo"). Plain substring lists miss cases like the first one
# because the noun comes after the subject, not right after the verb.
_IMAGE_CREATION_VERBS = re.compile(
    r"\b(generate|create|make|draw|design|render|paint|sketch)\b", re.I
)
_IMAGE_NOUNS = re.compile(
    r"\b(image|picture|photo|illustration|logo|artwork|icon|wallpaper|drawing|graphic|poster)s?\b",
    re.I,
)

TASK_TYPES = [
    "CODING", "REASONING", "RESEARCH", "WRITING", "IMAGE",
    "VISION", "DATA_ANALYSIS", "DOCUMENT_ANALYSIS", "GENERAL",
]

DIFFICULTIES = ["EASY", "MEDIUM", "HARD", "EXPERT"]

# Ordered so more specific categories are checked before GENERAL.
_TYPE_KEYWORDS = [
    ("IMAGE", [
        "generate an image", "draw", "illustration", "logo", "picture of",
        "image of", "artwork", "icon set", "wallpaper",
    ]),
    ("VISION", [
        "this image", "this photo", "this screenshot", "in the picture",
        "attached image", "what's in this image", "describe this image",
    ]),
    ("DOCUMENT_ANALYSIS", [
        "this pdf", "this document", "this contract", "this report",
        "summarize this file", "extract from this document",
    ]),
    ("DATA_ANALYSIS", [
        "csv", "dataframe", "spreadsheet", "dataset", "chart",
        "statistics", "regression", "correlation", "pandas", "sql query",
        "analyze this data",
    ]),
    ("CODING", [
        "code", "function", "bug", "debug", "api", "class ", "script",
        "python", "javascript", "flask", "react", "sql", "algorithm",
        "compile", "refactor", "unit test", "repository", "endpoint",
        "fix this", "implement",
    ]),
    ("RESEARCH", [
        "compare", "research", "latest", "state of the art", "survey",
        "pros and cons", "what are the differences", "literature",
        "benchmark",
    ]),
    ("WRITING", [
        "write a", "blog post", "essay", "article", "email", "story",
        "poem", "copywriting", "rewrite", "proofread", "tagline",
    ]),
    ("REASONING", [
        "prove", "solve", "why does", "logic", "puzzle", "reasoning",
        "step by step", "explain why", "derive",
    ]),
]

_HARD_SIGNALS = [
    "production-ready", "production ready", "enterprise", "scalable",
    "distributed", "fault-tolerant", "fault tolerant", "hybrid retrieval",
    "reranking", "evaluation pipeline", "architecture", "end to end",
    "end-to-end", "microservice", "concurrent", "authentication api",
]
_EXPERT_SIGNALS = [
    "formal proof", "novel algorithm", "research paper", "from first principles",
    "prove that", "publishable", "state-of-the-art system",
]
_EASY_SIGNALS = [
    "what is", "define", "explain briefly", "simple", "quick question",
    "one line", "one-liner", "short answer",
]


def classify_type(task: str) -> str:
    t = task.lower()

    # Check the verb+noun combo first — it catches phrasings like
    # "create a bird image" that the fixed phrase list below would miss.
    if _IMAGE_CREATION_VERBS.search(t) and _IMAGE_NOUNS.search(t):
        return "IMAGE"

    for task_type, keywords in _TYPE_KEYWORDS:
        for kw in keywords:
            if kw in t:
                return task_type
    return "GENERAL"


def classify_difficulty(task: str) -> str:
    t = task.lower()
    word_count = len(re.findall(r"\w+", task))

    if any(sig in t for sig in _EXPERT_SIGNALS):
        return "EXPERT"
    if any(sig in t for sig in _HARD_SIGNALS):
        return "HARD"
    if any(sig in t for sig in _EASY_SIGNALS) and word_count < 25:
        return "EASY"

    # Fall back to length/complexity as a rough proxy.
    if word_count <= 12:
        return "EASY"
    if word_count <= 40:
        return "MEDIUM"
    if word_count <= 90:
        return "HARD"
    return "EXPERT"


def analyze(task: str) -> dict:
    return {
        "task_type": classify_type(task),
        "difficulty": classify_difficulty(task),
        "word_count": len(re.findall(r"\w+", task)),
    }
