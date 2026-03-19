from openai import OpenAI

client = OpenAI(base_url="https://ollama.fit.fraunhofer.de/api",
               api_key="sk-39f498e276294f96a8cefdf9ac16fa12") # Den generierten API-Key verwenden

response = client.chat.completions.create(
   model="mistral:7b", # Ein verfügbares Modell aus Ollama wählen
   messages=[
       {"role": "system", "content": "Du bist ein hilfreicher Assitent."},
       {"role": "user", "content": "Wer war der erste Deutsche Bundeskanzler?"},
       {"role": "assistant", "content": "Der erste Deutsche Bundeskanzler war Konrad Adenauer . Er hat den Posten vom 1. Januar 1949 bis zum 26. Juli 1963 innegehabt."},
       {"role": "user", "content": "Erstelle mir eine Liste aller Deutschen Bundeskanzler."}
   ]
)
print(response.choices[0].message.content)
