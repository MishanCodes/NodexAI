import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

import orchestrator
import availability as availability_mod
from providers import REGISTRY

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "modelpilot-dev-secret")


@app.route("/")
def index():
    provider_meta = {
        name: {
            "model_name": provider.model_name,
            "demo": availability_mod.is_demo(name),
        }
        for name, provider in REGISTRY.items()
    }
    return render_template("index.html", provider_meta=provider_meta)


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(force=True) or {}
    task_text = (data.get("task") or "").strip()
    simulate_failure_on = set(data.get("simulate_failure_on") or [])

    if not task_text:
        return jsonify({"error": "Task text is required."}), 400

    result = orchestrator.run_task(task_text, simulate_failure_on=simulate_failure_on)
    return jsonify(result)


@app.route("/api/providers", methods=["GET"])
def api_providers():
    avail = availability_mod.check_all(list(REGISTRY.keys()))
    out = {}
    for name, provider in REGISTRY.items():
        out[name] = {
            "model_name": provider.model_name,
            "demo": avail[name]["demo"],
            "available": avail[name]["available"],
        }
    return jsonify(out)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
