import os
from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from rag import load_faiss_store, retrieve


app = Flask(__name__)

FAISS_PATH = os.path.join("data", "index.faiss")
PKL_PATH   = os.path.join("data", "index.pkl")

store = load_faiss_store(FAISS_PATH, PKL_PATH)
client = OpenAI()

SYSTEM_INSTRUCTIONS = (
    "You are a helpful chatbot for an NLP project. "
    "Answer using the provided context. "
    "If the context does not contain the answer, say you don't know and ask a follow-up question."
)

def build_context(docs):
    lines = []
    for i, d in enumerate(docs, start=1):
        meta = d.metadata or {}
        source = meta.get("source") or meta.get("file_name") or meta.get("path") or "unknown"
        page = meta.get("page")
        tag = f"{source}" + (f", page {page}" if page is not None else "")
        lines.append(f"[Source {i}: {tag}]\n{d.page_content}")
    return "\n\n".join(lines)

@app.post("/chat")
def chat():
    data = request.get_json(force=True)
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    docs = retrieve(store, user_message, k=4)
    context = build_context(docs)

    prompt = (
        f"CONTEXT:\n{context}\n\n"
        f"USER QUESTION:\n{user_message}\n\n"
        "INSTRUCTIONS:\n"
        "- Use only the context to answer.\n"
        "- If missing, say you don't know.\n"
        "- Keep the answer clear and direct.\n"
    )

    # OpenAI recommends Responses API for new projects. :contentReference[oaicite:3]{index=3}
    resp = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": prompt},
        ],
    )

    return jsonify({
        "answer": resp.output_text,
        "sources": [
            {"metadata": (d.metadata or {}), "snippet": d.page_content[:200]}
            for d in docs
        ]
    })

@app.get("/")
def home():
    return render_template("index.html")
if __name__ == "__main__":
    app.run(debug=True)