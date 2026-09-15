import os
import time
import uuid

from .base import BaseProvider, ProviderResult, GENERATED_DIR


class GeminiProvider(BaseProvider):
    """
    Google Gemini provider.

    Text tasks use the Gemini text model.
    Image tasks use Gemini's native image-generation model.
    """

    name = "gemini"

    # Text model
    model_name = "gemini-3.6-flash"

    # Native image-generation model
    image_model_name = "gemini-3.1-flash-image"

    # Gemini now has a real image-generation API
    can_generate_images = True

    def generate(self, task, context, demo, force_fail=False):
        """
        Generate text using Gemini.
        """

        if demo:
            return self._simulate(task, context, force_fail)

        if force_fail:
            return ProviderResult(
                success=False,
                error="Simulated timeout after partial generation (demo trigger).",
                model_name=self.model_name,
            )

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            return ProviderResult(
                success=False,
                error="GEMINI_API_KEY is not configured.",
                model_name=self.model_name,
            )

        try:
            from google import genai

            client = genai.Client(api_key=api_key)

            prompt = task

            # Recovery context
            if context.get("previous_partial_output"):
                prompt = (
                    f"{context.get('instruction', '')}\n\n"
                    f"Original task: {context.get('original_task', task)}\n\n"
                    f"Previous model ({context.get('previous_model')}) produced:\n"
                    f"{context.get('previous_partial_output')}\n\n"
                    f"It stopped because: {context.get('error')}\n\n"
                    f"Continue the task from the previous result. "
                    f"Do not unnecessarily restart the entire task."
                )

            start = time.time()

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            latency_ms = int((time.time() - start) * 1000)

            content = getattr(response, "text", None)

            if not content:
                content = "Gemini returned an empty response."

            return ProviderResult(
                success=True,
                content=content,
                model_name=self.model_name,
                latency_ms=latency_ms,
                content_type="text",
            )

        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                model_name=self.model_name,
                content_type="text",
            )

    def generate_image(self, task, context, demo, force_fail=False):
        """
        Generate a real image using Gemini's native image-generation API.
        """

        if demo:
            return self._simulate_image(task)

        if force_fail:
            return ProviderResult(
                success=False,
                error="Simulated image-generation failure (demo trigger).",
                model_name=self.image_model_name,
                content_type="image",
            )

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            return ProviderResult(
                success=False,
                error="GEMINI_API_KEY is not configured.",
                model_name=self.image_model_name,
                content_type="image",
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            start = time.time()

            response = client.models.generate_content(
                model=self.image_model_name,
                contents=task,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"]
                ),
            )

            latency_ms = int((time.time() - start) * 1000)

            # Find the generated image in the response.
            for part in response.parts:

                if part.inline_data is not None:
                    image = part.as_image()

                    filename = f"{uuid.uuid4().hex[:12]}.png"
                    path = os.path.join(GENERATED_DIR, filename)

                    image.save(path)

                    return ProviderResult(
                        success=True,
                        content=f"/static/generated/{filename}",
                        model_name=self.image_model_name,
                        latency_ms=latency_ms,
                        content_type="image",
                    )

            return ProviderResult(
                success=False,
                error="Gemini completed the request but returned no image.",
                model_name=self.image_model_name,
                latency_ms=latency_ms,
                content_type="image",
            )

        except Exception as e:
            return ProviderResult(
                success=False,
                error=str(e),
                model_name=self.image_model_name,
                content_type="image",
            )