"""
Common provider interface. The orchestrator only ever calls
`provider.generate(task, context)` (text) or `provider.generate_image(...)`
(image tasks) — it never knows about SDKs, auth, or per-vendor request shapes.
"""
import os
import random
import time
import uuid


GENERATED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)


class ProviderResult:
    def __init__(self, success, content="", error="", model_name="", latency_ms=0, content_type="text"):
        self.success = success
        self.content = content
        self.error = error
        self.model_name = model_name
        self.latency_ms = latency_ms
        self.content_type = content_type  # "text" or "image"

    def to_dict(self):
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error,
            "model_name": self.model_name,
            "latency_ms": self.latency_ms,
            "content_type": self.content_type,
        }


class BaseProvider:
    name = "base"
    model_name = "base-model"
    can_generate_images = False  # only providers that override generate_image with a real API call set this True

    def generate(self, task: str, context: dict, demo: bool, force_fail: bool = False) -> ProviderResult:
        raise NotImplementedError

    def generate_image(self, task: str, context: dict, demo: bool, force_fail: bool = False) -> ProviderResult:
        """Default: this provider has no real image-generation API (it's a
        text model), so it's honest about that rather than faking a text
        response for an image task. Providers with a real image endpoint
        (OpenAI, Grok) override this."""
        if force_fail:
            return ProviderResult(
                success=False,
                error="Simulated failure (demo trigger).",
                model_name=self.model_name,
                content_type="image",
            )
        return self._simulate_image(task)

    # --- shared demo-mode helper -------------------------------------
    def _simulate(self, task: str, context: dict, force_fail: bool):
        """Every provider falls back to this when it has no API key
        (or FORCE_DEMO_MODE is on) so the full pipeline is always
        demoable without any internet access or keys."""
        time.sleep(random.uniform(0.4, 0.9))  # feel like a real call

        if force_fail:
            return ProviderResult(
                success=False,
                error="Simulated timeout after partial generation (demo trigger).",
                model_name=self.model_name,
                latency_ms=int(random.uniform(2000, 4000)),
            )

        if context.get("previous_partial_output"):
            content = (
                f"[continuing from {context.get('previous_model')}]\n"
                f"Picked up after: {context.get('error')}\n"
                f"Completed the remaining steps for: \"{task[:80]}\""
            )
        else:
            content = f"[{self.name} demo output] Completed: \"{task[:80]}\""

        return ProviderResult(
            success=True,
            content=content,
            model_name=self.model_name,
            latency_ms=int(random.uniform(500, 1500)),
        )

    def _simulate_image(self, task: str) -> ProviderResult:
        """Draws a plain placeholder PNG with the prompt text on it —
        used when a provider has no real image-generation API at all
        (Claude/Gemini/Groq are text-only), or when one that DOES have
        one (OpenAI/Grok) has no key configured yet. No internet or API
        key required, so the pipeline is always demoable."""
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        time.sleep(random.uniform(0.5, 1.0))

        w, h = 640, 640
        img = Image.new("RGB", (w, h), color=(18, 22, 31))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w - 1, h - 1], outline=(70, 78, 100), width=2)

        try:
            font_label = ImageFont.load_default(size=18)
            font_body = ImageFont.load_default(size=22)
            font_footer = ImageFont.load_default(size=14)
        except TypeError:
            # Older Pillow without the size= kwarg on load_default.
            font_label = font_body = font_footer = ImageFont.load_default()

        label = f"{self.name} (demo)"
        wrapped = textwrap.fill(task, width=26)

        if self.can_generate_images:
            footer = "[simulated - no API key configured yet; add one for a real image]"
        else:
            footer = "[simulated - this model has no real image-generation API]"

        draw.text((24, 22), label, fill=(139, 147, 167), font=font_label)
        draw.multiline_text((24, 60), wrapped, fill=(230, 233, 239), font=font_body, spacing=8)
        draw.multiline_text((24, h - 56), textwrap.fill(footer, width=48), fill=(212, 87, 74), font=font_footer, spacing=4)

        filename = f"{uuid.uuid4().hex[:12]}.png"
        path = os.path.join(GENERATED_DIR, filename)
        img.save(path)

        return ProviderResult(
            success=True,
            content=f"/static/generated/{filename}",
            model_name=self.model_name,
            latency_ms=int(random.uniform(500, 1200)),
            content_type="image",
        )
