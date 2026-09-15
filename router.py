"""
Smart Router
------------
Combines task type + difficulty + a capability matrix + live
availability to pick the best provider. Never hardcodes
"type -> provider"; every selection is a score.
"""

# Per-provider capability score (1-5) per task type. Illustrative
# starting values from the design doc — meant to be recalibrated
# once real usage data comes in (see README).
CAPABILITY_MATRIX = {
    "claude":  {"CODING": 5, "REASONING": 5, "RESEARCH": 4, "WRITING": 5,
                "IMAGE": 1, "VISION": 4, "DATA_ANALYSIS": 4, "DOCUMENT_ANALYSIS": 5, "GENERAL": 5},
    "gemini":  {"CODING": 4, "REASONING": 4, "RESEARCH": 4, "WRITING": 4,
                "IMAGE": 2, "VISION": 5, "DATA_ANALYSIS": 4, "DOCUMENT_ANALYSIS": 4, "GENERAL": 4},
    "groq":    {"CODING": 4, "REASONING": 3, "RESEARCH": 3, "WRITING": 3,
                "IMAGE": 1, "VISION": 2, "DATA_ANALYSIS": 3, "DOCUMENT_ANALYSIS": 3, "GENERAL": 4},
    "openai":  {"CODING": 5, "REASONING": 5, "RESEARCH": 4, "WRITING": 5,
                "IMAGE": 5, "VISION": 4, "DATA_ANALYSIS": 4, "DOCUMENT_ANALYSIS": 4, "GENERAL": 5},
    "grok":    {"CODING": 3, "REASONING": 4, "RESEARCH": 4, "WRITING": 3,
                "IMAGE": 5, "VISION": 3, "DATA_ANALYSIS": 3, "DOCUMENT_ANALYSIS": 3, "GENERAL": 4},
}

# Speed matters more as difficulty drops (an EASY task shouldn't wait on
# a slow model); accuracy/capability matters more as difficulty rises.
SPEED_SCORE = {"claude": 4, "gemini": 4, "groq": 5, "openai": 4, "grok": 4}

DIFFICULTY_WEIGHT = {
    "EASY":   {"capability": 0.5, "speed": 0.5},
    "MEDIUM": {"capability": 0.7, "speed": 0.3},
    "HARD":   {"capability": 0.85, "speed": 0.15},
    "EXPERT": {"capability": 0.95, "speed": 0.05},
}


def score_provider(provider: str, task_type: str, difficulty: str) -> float:
    cap = CAPABILITY_MATRIX.get(provider, {}).get(task_type, 3)
    speed = SPEED_SCORE.get(provider, 3)
    weights = DIFFICULTY_WEIGHT.get(difficulty, DIFFICULTY_WEIGHT["MEDIUM"])
    return round((cap * weights["capability"] + speed * weights["speed"]) * 20, 1)  # 0-100 scale


def rank_providers(task_type: str, difficulty: str, availability: dict, exclude=None) -> list:
    """Returns a list of {provider, score, available, demo} sorted
    best-first. Unavailable / excluded providers are still listed (with
    score) so the UI can show *why* something wasn't picked — just not
    eligible for selection.

    Ranking: any live provider (real API key configured) outranks any
    demo/simulated one, full stop — not just as a tie-break. A demo
    provider can't produce a real result, so a high capability score on
    paper shouldn't beat a lower-scoring provider that can actually run.
    Demo providers are only ever selected when no live provider is
    eligible (e.g. every live one has failed and been excluded, or none
    were configured at all) — which keeps the "runs with zero keys"
    behavior intact for a from-scratch demo.
    """
    exclude = exclude or set()
    ranked = []
    for provider in CAPABILITY_MATRIX:
        score = score_provider(provider, task_type, difficulty)
        info = availability.get(provider, {})
        available = info.get("available", False)
        demo = info.get("demo", True)
        eligible = available and provider not in exclude
        ranked.append({
            "provider": provider,
            "score": score,
            "available": available,
            "demo": demo,
            "eligible": eligible,
        })
    # Primary: live before demo, regardless of score. Secondary: higher
    # score first, within each group.
    ranked.sort(key=lambda r: (r["demo"], -r["score"]))
    return ranked


def select_best(task_type: str, difficulty: str, availability: dict, exclude=None) -> dict | None:
    ranked = rank_providers(task_type, difficulty, availability, exclude=exclude)
    for r in ranked:
        if r["eligible"]:
            return r
    return None
