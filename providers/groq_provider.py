import os
import time
from .base import BaseProvider, ProviderResult


class GroqProvider(BaseProvider):
    name = "groq"
    model_name = "openai/gpt-oss-120b"

    def generate(self, task, context, demo, force_fail=False):
        if demo:
            return self._simulate(task, context, force_fail)

        try:
            from groq import Groq
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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
            resp = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
            )
            latency_ms = int((time.time() - start) * 1000)
            content = resp.choices[0].message.content
            return ProviderResult(True, content=content, model_name=self.model_name, latency_ms=latency_ms)
        except Exception as e:
            return ProviderResult(False, error=str(e), model_name=self.model_name)
