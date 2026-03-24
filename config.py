import os

# LLM Backend configuration - set via env vars
OLLAMA_URL = os.environ.get("OLLAMA_URL", "https://ollama.fit.fraunhofer.de/api")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral:7b")

# Pipeline defaults
TOP_K = 5
INTENT = "annotation"

INSTRUCTION = {
    "annotation": "Provide the most accurate description and unit for the term in user query by identifying its meaning according to retrieved content from public knowledge bases.",
    "query": "Answer user questions in user query by querying and retrieving relevant content from the internal pilot database.",
    "decision": "Validate the reliability of decision-making actions mentioned in user query according to retrieved content from relevant pilot databases."
}
