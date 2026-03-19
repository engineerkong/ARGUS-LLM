import struct
import re
from types import SimpleNamespace

from wikidata import WikidataNativeSearchRetriever
from gpkg_database import GPKGTableRetriever
from prompt_templates import build_augmented_prompt
from llm_client import LLMClient
from config import INSTRUCTION, TOP_K, INTENT, OLLAMA_MODEL


def _decode_gpkg_binary(data):
    if not data or len(data) < 8 or data[0:2] != b'GP':
        return None
    flags = data[3]
    env_size = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}.get((flags >> 1) & 0x07, 0)
    wkb = data[8 + env_size:]
    if not wkb:
        return None
    bo = '<' if wkb[0] == 1 else '>'
    geom_type = struct.unpack(f'{bo}I', wkb[1:5])[0]
    try:
        if geom_type == 1:
            x, y = struct.unpack(f'{bo}d', wkb[5:13])[0], struct.unpack(f'{bo}d', wkb[13:21])[0]
            return f"({x:.6f}, {y:.6f})"
        elif geom_type == 4:
            n = struct.unpack(f'{bo}I', wkb[5:9])[0]
            coords, off = [], 9
            for _ in range(n):
                x = struct.unpack(f'{bo}d', wkb[off+5:off+13])[0]
                y = struct.unpack(f'{bo}d', wkb[off+13:off+21])[0]
                coords.append(f"({x:.6f}, {y:.6f})")
                off += 21
            return ", ".join(coords)
    except Exception:
        pass
    return None


def _process_geometries(retrieved):
    processed = []
    for doc in retrieved:
        if hasattr(doc, 'text'):
            text = re.sub(
                r"b'(GP[^']+)'",
                lambda m: _decode_gpkg_binary(
                    m.group(1).encode('latin1').decode('unicode_escape').encode('latin1')
                ) or m.group(0),
                doc.text
            )
            try:
                doc = type(doc)(**{**doc.__dict__, 'text': text})
            except Exception:
                pass
        processed.append(doc)
    return processed


class RAGPipeline:
    def __init__(self, model: str = None, pilot_gpkg: str = None):
        effective_model = model or OLLAMA_MODEL
        self.llm = LLMClient(model=effective_model)
        self.external_retriever = WikidataNativeSearchRetriever(model=effective_model)
        self.pilot_gpkg = pilot_gpkg
        self.internal_retriever = GPKGTableRetriever(pilot_gpkg) if pilot_gpkg else None

    def set_gpkg(self, path: str):
        if path and path != self.pilot_gpkg:
            self.pilot_gpkg = path
            self.internal_retriever = GPKGTableRetriever(path)

    def run_query(self, query: str, intent: str = INTENT, top_k: int = TOP_K, dataset_path: str = None):
        if dataset_path:
            self.set_gpkg(dataset_path)

        if intent == "annotation":
            retrieved = self.external_retriever.find_explanations(query)
        elif intent in ("query", "decision"):
            if not self.internal_retriever:
                raise ValueError(
                    "No internal database configured. Provide a Dataset Path (GPKG file)."
                )
            retrieved = self.internal_retriever.retrieve(query)
        else:
            raise ValueError(f"Unknown intent: {intent}")

        retrieved = _process_geometries(retrieved)

        instructions = INSTRUCTION.get(intent, "") + " Be concise (1-3 sentences)."
        prompt = build_augmented_prompt(intent, query, retrieved, instructions=instructions)
        response = self.llm.generate(prompt)

        if not retrieved:
            response += "\n\n[Note] No retrieved documents found; answer may be speculative."

        return {
            "intent": intent,
            "retrieved": retrieved,
            "response": response
        }
