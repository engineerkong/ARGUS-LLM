import os
from xml.parsers.expat import model
from openai import OpenAI


class LLMClient:
    def __init__(self, base_url: str = None, api_key: str = None, model: str = "mistral:7b"):
        self.base_url = base_url or os.environ.get("OLLAMA_URL", "https://ollama.fit.fraunhofer.de/api")
        self.api_key = api_key or os.environ.get("OLLAMA_API_KEY", "sk-39f498e276294f96a8cefdf9ac16fa12")
        self.model = model
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: str = "You are a cultural heritage expert. Answer the following questions accurately and concisely, using the retrieved information where relevant.", max_tokens: int = 512, temperature: float = 0.0) -> str:
        print(f"LLMClient initialized with base_url={self.base_url}, model={self.model}")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[LLM Error] Request failed: {e}"
