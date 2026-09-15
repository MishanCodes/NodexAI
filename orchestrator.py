"""
Orchestrator
------------
Runs the full ModelPilot loop for one task and returns a step-by-step
trace the UI can render as a pipeline. This is the only module that
calls into router / availability / memory / providers together.
"""
import classifier
import router
import availability as availability_mod
import memory
from providers import REGISTRY

ALL_PROVIDERS = list(REGISTRY.keys())
MAX_ATTEMPTS = len(ALL_PROVIDERS)  # never loop forever


def run_task(task_text: str, simulate_failure_on: set | None = None) -> dict:
    simulate_failure_on = simulate_failure_on or set()
    trace = []

    # 1. Task analysis
    analysis = classifier.analyze(task_text)
    task_type, difficulty = analysis["task_type"], analysis["difficulty"]
    trace.append({
        "stage": "analysis",
        "label": "Task Analyzer",
        "detail": {"task_type": task_type, "difficulty": difficulty, "word_count": analysis["word_count"]},
    })

    task_id = memory.new_task(task_text, task_type, difficulty)

    # 2. Availability check
    # Note: simulate_failure_on is NOT applied here. A "simulated failure"
    # should still be picked by the router (it looks fully available/
    # eligible), actually attempt execution, and THEN fail mid-task —
    # that's what makes the recovery engine kick in below. Marking it
    # unavailable up front would just make the router skip it silently.
    avail = availability_mod.check_all(ALL_PROVIDERS)
    trace.append({
        "stage": "availability",
        "label": "Provider Availability",
        "detail": avail,
    })

    # 3. Router scoring
    ranked = router.rank_providers(task_type, difficulty, avail)
    trace.append({
        "stage": "routing",
        "label": "Smart Router",
        "detail": {"ranked": ranked},
    })

    excluded = set()
    attempts = 0
    final_result = None

    # Loop until every provider has been excluded (tried-and-failed or
    # ineligible) rather than a fixed attempt count, so the "all
    # providers exhausted" branch below is always reachable.
    while len(excluded) <= len(ALL_PROVIDERS):
        attempts += 1
        choice = router.select_best(task_type, difficulty, avail, exclude=excluded)

        if choice is None:
            trace.append({
                "stage": "exhausted",
                "label": "No Providers Left",
                "detail": {"message": "All providers unavailable or failed. Task cannot complete."},
            })
            memory.set_status(task_id, "failed")
            break

        provider_name = choice["provider"]
        provider = REGISTRY[provider_name]
        demo = availability_mod.is_demo(provider_name)
        force_fail = provider_name in simulate_failure_on

        trace.append({
            "stage": "selection",
            "label": "Model Selected",
            "detail": {"provider": provider_name, "score": choice["score"], "demo": demo, "attempt": attempts},
        })

        context = memory.build_recovery_context(task_id) if task_id and memory.get_task(task_id)["history"] else {}

        if task_type == "IMAGE":
            result = provider.generate_image(task_text, context, demo=demo, force_fail=force_fail)
        else:
            result = provider.generate(task_text, context, demo=demo, force_fail=force_fail)

        history_entry = {
            "model": provider_name,
            "status": "success" if result.success else "failed",
            "content": result.content,
            "content_type": result.content_type,
            "error": result.error,
            "latency_ms": result.latency_ms,
            "demo": demo,
        }
        memory.add_history(task_id, history_entry)

        trace.append({
            "stage": "execution",
            "label": f"{provider_name} executing",
            "detail": history_entry,
        })

        if result.success:
            memory.set_status(task_id, "success")
            final_result = history_entry
            break
        else:
            # Failure -> recovery engine
            excluded.add(provider_name)
            trace.append({
                "stage": "recovery",
                "label": "Recovery Engine",
                "detail": {
                    "failed_provider": provider_name,
                    "error": result.error,
                    "message": "Previous response and task state recovered from shared memory. "
                               "Checking availability for next best model.",
                },
            })

    task_state = memory.get_task(task_id)

    return {
        "task_id": task_id,
        "task_type": task_type,
        "difficulty": difficulty,
        "trace": trace,
        "final_result": final_result,
        "status": task_state["status"] if task_state else "unknown",
        "attempts": attempts,
    }
