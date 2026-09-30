import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai
from google.genai import types
from chatbot_config import CHATBOT_TITLE, STUDY_DOMAIN, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

MODEL_NAME = "gemini-3.1-flash-lite"
api_key = os.getenv("GEMINI_API_KEY", "").strip()
client = genai.Client(api_key=api_key) if api_key else None


def build_prompt(message, history):
    recent = history[-10:] if isinstance(history, list) else []
    conversation = []
    for item in recent:
        if not isinstance(item, dict):
            continue
        role = item.get("role", "")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            conversation.append(f"{role.upper()}: {content}")

    context = "\n".join(conversation)
    if context:
        return f"Previous conversation:\n{context}\n\nUSER: {message}\n\nAnswer the USER according to your system instructions."
    return f"USER: {message}\n\nAnswer the USER according to your system instructions."


@app.get("/")
def home():
    return render_template("index.html", chatbot_title=CHATBOT_TITLE, study_domain=STUDY_DOMAIN)


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a message."}), 400

    if client is None:
        return jsonify({"error": "GEMINI_API_KEY is not configured."}), 503

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_prompt(message, history),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.35,
            ),
        )
        answer = (response.text or "").strip()
        if not answer:
            answer = "I could not generate a response. Please try again."
        return jsonify({"answer": answer})
    except Exception as exc:
        return jsonify({"error": f"Unable to process the request: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
