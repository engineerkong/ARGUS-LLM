from flask import Flask, render_template, request, jsonify
import os
import traceback
from config import OLLAMA_MODEL
from pipeline import RAGPipeline

app = Flask(__name__, template_folder="templates", static_folder="static")

# Global pipeline cache keyed by (model, gpkg)
_pipeline_cache: dict = {}


def get_pipeline(model: str, pilot_gpkg: str = None) -> RAGPipeline:
    key = (model, pilot_gpkg or "")
    if key not in _pipeline_cache:
        _pipeline_cache.clear()  # keep only latest
        _pipeline_cache[key] = RAGPipeline(model=model, pilot_gpkg=pilot_gpkg or None)
    return _pipeline_cache[key]


@app.route("/")
def index():
    return render_template("index.html", default_model=OLLAMA_MODEL)


@app.route("/api/query", methods=["POST"])
def api_query():
    try:
        data = request.get_json(force=True)
        query = (data.get("query") or "").strip()
        intent = data.get("intent", "annotation")
        top_k = int(data.get("top_k", 5))
        model = (data.get("model") or OLLAMA_MODEL).strip()
        dataset_path = (data.get("dataset_path") or "").strip() or None

        if not query:
            return jsonify({"error": "query is required"}), 400

        pipeline = get_pipeline(model, dataset_path)
        result = pipeline.run_query(query, intent=intent, top_k=top_k, dataset_path=dataset_path)

        retrieved = result.get("retrieved", [])
        serialized = []
        for d in retrieved:
            serialized.append({
                "text": getattr(d, "text", str(d)),
                "source": getattr(d, "source", None),
                "score": getattr(d, "score", None)
            })

        return jsonify({
            "intent": result.get("intent"),
            "retrieved": serialized,
            "response": result.get("response")
        })

    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/config", methods=["GET"])
def api_config():
    """Return current server-side defaults for the UI."""
    return jsonify({"model": OLLAMA_MODEL})


if __name__ == "__main__":
    host = os.environ.get("WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("WEB_PORT", "5000"))
    app.run(host=host, port=port, debug=True)
