# Prompt templates for augmentation and source formatting

from typing import List, Dict

def format_sources(retrieved: List[Dict]) -> str:
    parts = []
    for i, r in enumerate(retrieved, start=1):
        parts.append(f"[{i}] Source: {r.source}\nScore: {r.score:.3f}\nExcerpt: {r.text}\n")
    return "\n".join(parts)

def build_augmented_prompt(intent: str, user_query: str, retrieved: List[Dict], instructions: str = "") -> str:
    sources_block = format_sources(retrieved)
    prompt = f"""You are an assistant. Follow instructions: {instructions}

User query:
{user_query} [{intent}]

Retrieved context (with sources):
{sources_block}

Please answer the user's query, synthesize information from the retrieved context, and include inline citations from retrieved context like [1], [2]. If the answer cannot be determined, say so and list the sources consulted.
"""
    return prompt
