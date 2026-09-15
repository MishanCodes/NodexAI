import os
import time
import uuid
from .base import BaseProvider, ProviderResult, GENERATED_DIR


class OpenAIProvider(BaseProvider):
    name = "openai"
    model_name = "gpt-4o-mini"
    image_model_name = "dall-e-3"
    can_generate_images = True

    def generate(self, task, context, demo, force_fail=False):
        if demo:
            return self._simulate(task, context, force_fail)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

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

    def generate_image(self, task, context, demo, force_fail=False):
        if demo:
            return self._simulate_image(task)
        if force_fail:
            return ProviderResult(False, error="Simulated timeout (demo trigger).",
                                   model_name=self.image_model_name, content_type="image")

        try:
            import requests
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            start = time.time()
            resp = client.images.generate(
                model=self.image_model_name,
                prompt=task,
                size="1024x1024",
                n=1,
            )
            latency_ms = int((time.time() - start) * 1000)

            image_url = resp.data[0].url
            img_bytes = requests.get(image_url, timeout=30).content

            filename = f"{uuid.uuid4().hex[:12]}.png"
            path = os.path.join(GENERATED_DIR, filename)
            with open(path, "wb") as f:
                f.write(img_bytes)

            return ProviderResult(
                True, content=f"/static/generated/{filename}",
                model_name=self.image_model_name, latency_ms=latency_ms, content_type="image",
            )
        except Exception as e:
            return ProviderResult(False, error=str(e), model_name=self.image_model_name, content_type="image")
