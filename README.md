# NodexAI

### Intelligent Multi-Model Routing & Recovery

**NodexAI** is a **Version 1 prototype** of a multi-LLM orchestration system that connects multiple AI providers through a single interface.

Instead of relying on one model, NodexAI analyzes a task, selects a suitable provider, checks availability, and can automatically switch to another provider when the selected model fails.

> **One task → Best available model → Automatic recovery**

---

## 🚀 How It Works

```text
User Task
   ↓
Task Classification
   ↓
Provider Availability
   ↓
Intelligent Router
   ↓
Best Provider
   ↓
Execute Task
   ↓
Success?
 ┌─┴─┐
Yes  No
 ↓    ↓
Result  Recovery
        ↓
   Next Provider
```

NodexAI also passes relevant previous output and failure information to the next provider during recovery.

---

## ✨ Features

* 🤖 Multi-LLM provider support
* 🧠 Task type & difficulty classification
* 🔀 Intelligent provider routing
* 🔄 Automatic failure recovery
* 🧩 Context handoff between models
* 🖼️ Text and image task routing
* 🩺 Provider availability checking
* 🧪 Demo mode and simulated failures
* 🔐 Environment-based API key management

---

## 🔌 Supported Providers

| Provider         | Text | Image |
| ---------------- | ---- | ----- |
| Anthropic Claude | ✅    | ❌     |
| Google Gemini    | ✅    | ✅*    |
| Groq             | ✅    | ❌     |
| OpenAI           | ✅    | ✅     |
| xAI Grok         | ✅    | ✅     |

* Depends on model availability, quota, and API access.

---

## 🏗️ Tech Stack

**Backend:** Python, Flask
**AI:** Claude, Gemini, Groq, OpenAI, Grok
**Image:** Pillow
**API:** Requests, HTTPX
**Deployment:** Gunicorn, Render

---

## 📂 Project Structure

```text
NodexAI/
├── app.py
├── orchestrator.py
├── classifier.py
├── router.py
├── availability.py
├── memory.py
│
├── providers/
│   ├── base.py
│   ├── anthropic_provider.py
│   ├── gemini_provider.py
│   ├── groq_provider.py
│   ├── openai_provider.py
│   └── grok_provider.py
│
├── templates/
├── static/
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Run Locally

```bash
git clone https://github.com/MishanCodes/NodexAI.git
cd NodexAI

python -m venv myenv
myenv\Scripts\activate

python -m pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5050
```

Add your API keys to `.env`. NodexAI can also run in demo mode without provider keys.

---

## ☁️ Deployment

NodexAI can be deployed on **Render**.

**Build Command:**

```bash
pip install -r requirements.txt
```

**Start Command:**

```bash
gunicorn app:app
```

API keys should be added through Render's environment variables and should never be committed to GitHub.

---

## 🧪 Version 1 / Prototype

NodexAI is currently **Version 1 (prototype)**.

The current version focuses on proving the core concept:

**Task understanding → Model selection → Execution → Failure detection → Model recovery**

Future versions can introduce smarter ML-based routing, cost/latency optimization, persistent memory, streaming, authentication, analytics, and additional providers.

---

## 👨‍💻 Author

**Mishanraj Kalita**
B.Tech Computer Science & Engineering

Interested in **AI/ML, Generative AI, LLM Applications, and Python Backend Development**.

---

⭐ **NodexAI — Version 1 Prototype**
