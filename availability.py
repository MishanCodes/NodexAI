"""
Availability Check
-------------------
Determines whether each provider can actually be used right now.

A provider is "available" if either:
  - it has an API key configured (real calls will be attempted), or
  - DEMO_MODE is on for it, in which case it's always "available" and
    simulates a response instead of skipping the demo entirely.

This module never makes the actual generation call — that's the
provider's job. It only decides eligibility for the router.
"""
import os

PROVIDER_ENV_KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "grok": "GROK_API_KEY",
}


def force_demo_mode() -> bool:
    return os.environ.get("FORCE_DEMO_MODE", "false").strip().lower() in (
        "1", "true", "yes", "on",
    )


def has_real_key(provider: str) -> bool:
    env_key = PROVIDER_ENV_KEYS.get(provider)
    if not env_key:
        return False
    return bool(os.environ.get(env_key, "").strip())


def is_demo(provider: str) -> bool:
    """A provider runs in demo/simulated mode if forced globally, or if
    it simply has no API key configured. Either way it stays *available*
    — this is the resilience property from the spec: no provider is
    ever mandatory."""
    return force_demo_mode() or not has_real_key(provider)


def check_all(providers, fail_overrides=None) -> dict:
    """
    fail_overrides: optional set of provider names to force-mark as
    unavailable, used only by the demo's "simulate a failure" control
    so the recovery flow can be shown live and reliably.
    """
    fail_overrides = fail_overrides or set()
    result = {}
    for name in providers:
        if name in fail_overrides:
            result[name] = {"available": False, "reason": "simulated_outage", "demo": is_demo(name)}
        else:
            result[name] = {"available": True, "reason": "ok", "demo": is_demo(name)}
    return result
