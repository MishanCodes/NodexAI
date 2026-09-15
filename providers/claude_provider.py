import os
import time
from .base import BaseProvider, ProviderResult


class ClaudeProvider(BaseProvider):
    name = "claude"
    model_name = "claude-sonnet-4-6"

    def generate(self, task, context, demo, force_fail=False):
        if demo:
            return self._simulate(task, context, force_fail)

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

            prompt = task
            if context.get("previous_partial_output"):
                prompt = (
                    f"{context['instruction']}\n\n"
                    f"Original task: {context['original_task']}\n"
                    f"Previous model ({context.get('previous_model')}) produced:\n"
                    f"{context['previous_partial_output']}\n\n"
                    f"It stopped because: {context.get('error')}\n"
                    f"Continue the task now."
                )

            start = time.time()
            resp = client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            latency_ms = int((time.time() - start) * 1000)
            content = "".join(
                block.text for block in resp.content if getattr(block, "type", "") == "text"
            )
            return ProviderResult(True, content=content, model_name=self.model_name, latency_ms=latency_ms)
        except Exception as e:
            return ProviderResult(False, error=str(e), model_name=self.model_name)
