"""
Wikidata Native Search + LLM Assessment
=======================================

Uses Wikidata's built-in fuzzy and semantic search capabilities
combined with LLM for cultural heritage relevance assessment.
"""

import requests
import json
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TermExplanation:
    text: str
    score: float
    source: str

class WikidataNativeSearchRetriever:
    def __init__(self, model: str = "mistral:7b"):
        self.model = model
        self.wikidata_url = "https://www.wikidata.org/w/api.php"
        self.sparql_url = "https://query.wikidata.org/sparql"
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'WikidataSearch/1.0'})
    
    def search_exact(self, term: str) -> List[Dict]:
        """Exact search using Wikidata API"""
        params = {
            'action': 'wbsearchentities',
            'search': term,
            'language': 'en',
            'format': 'json',
            'limit': 10,
            'type': 'item'
        }
        
        try:
            response = self.session.get(self.wikidata_url, params=params)
            results = response.json().get('search', [])
            for result in results:
                result['search_type'] = 'exact'
            return results
        except:
            return []
    
    def search_fuzzy(self, term: str) -> List[Dict]:
        """Fuzzy search using Wikidata's SPARQL with regex and soundex"""
        
        # SPARQL query for fuzzy matching
        sparql_query = f"""
        SELECT ?item ?itemLabel ?itemDescription WHERE {{
          SERVICE wikibase:mwapi {{
            bd:serviceParam wikibase:api "EntitySearch" .
            bd:serviceParam wikibase:endpoint "www.wikidata.org" .
            bd:serviceParam mwapi:search "{term}" .
            bd:serviceParam mwapi:language "en" .
            ?item wikibase:apiOutputItem mwapi:item .
          }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
        }}
        LIMIT 10
        """
        
        try:
            response = self.session.get(self.sparql_url, params={
                'query': sparql_query,
                'format': 'json'
            })
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for binding in data.get('results', {}).get('bindings', []):
                    item_uri = binding.get('item', {}).get('value', '')
                    entity_id = item_uri.split('/')[-1] if item_uri else ''
                    
                    label = binding.get('itemLabel', {}).get('value', '')
                    description = binding.get('itemDescription', {}).get('value', '')
                    
                    if entity_id and label:
                        results.append({
                            'id': entity_id,
                            'label': label,
                            'description': description,
                            'search_type': 'fuzzy'
                        })
                
                return results
        except Exception as e:
            print(f"   ⚠️  SPARQL fuzzy search failed: {e}")
        
        return []
    
    def search_semantic(self, term: str) -> List[Dict]:
        """Semantic search using Wikidata's full-text search"""
        
        # Use Wikidata's CirrusSearch for semantic matching
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': f'"{term}" OR "{term.replace("_", " ")}" OR "{term.lower()}"',
            'srnamespace': '0',  # Main namespace
            'srlimit': 10,
            'srprop': 'snippet|titlesnippet'
        }
        
        try:
            response = self.session.get(self.wikidata_url, params=params)
            data = response.json()
            
            results = []
            for result in data.get('query', {}).get('search', []):
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                
                if title.startswith('Q') and title[1:].isdigit():  # Valid entity ID
                    results.append({
                        'id': title,
                        'search_type': 'semantic',
                        'snippet': snippet
                    })
            
            # Get full details for semantic search results
            detailed_results = []
            for result in results:
                details = self.get_entity_details(result['id'])
                if details.get('label'):
                    details['search_type'] = 'semantic'
                    detailed_results.append(details)
            
            return detailed_results
            
        except Exception as e:
            print(f"   ⚠️  Semantic search failed: {e}")
        
        return []
    
    def search_wikidata_full_text(self, term: str) -> List[Dict]:
        """Use Wikidata's MediaWiki full-text search"""
        
        # Alternative semantic search using opensearch
        params = {
            'action': 'opensearch',
            'search': term,
            'limit': 10,
            'namespace': 0,
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.wikidata_url, params=params)
            data = response.json()
            
            if len(data) >= 2:
                titles = data[1]  # List of page titles (entity IDs)
                results = []
                
                for title in titles:
                    if title.startswith('Q') and title[1:].isdigit():
                        details = self.get_entity_details(title)
                        if details.get('label'):
                            details['search_type'] = 'fulltext'
                            results.append(details)
                
                return results
        
        except Exception as e:
            print(f"   ⚠️  Full-text search failed: {e}")
        
        return []
    
    def get_entity_details(self, entity_id: str) -> Dict:
        """Get entity details from Wikidata"""
        params = {
            'action': 'wbgetentities',
            'ids': entity_id,
            'format': 'json',
            'languages': 'en',
            'props': 'labels|descriptions'
        }
        
        try:
            response = self.session.get(self.wikidata_url, params=params)
            data = response.json()
            
            if 'entities' in data and entity_id in data['entities']:
                entity = data['entities'][entity_id]
                
                label = ''
                if 'labels' in entity and 'en' in entity['labels']:
                    label = entity['labels']['en'].get('value', '')
                
                description = ''
                if 'descriptions' in entity and 'en' in entity['descriptions']:
                    description = entity['descriptions']['en'].get('value', '')
                
                return {'label': label, 'description': description, 'id': entity_id}
        except:
            pass
        
        return {}
    
    def assess_cultural_heritage_relevance(self, original_term: str, label: str, description: str) -> float:
        """Use keywords matching to assess cultural heritage relevance"""

        text = (label + " " + description).lower()
        cultural_words = ['preservation', 'conservation', 'restoration', 'archaeology', 'excavation', 'antiquity', 
                        'relic', 'manuscript', 'folklore', 'tradition', 'customs', 'ritual', 'ceremony', 'legacy', 
                        'ancestry', 'genealogy', 'documentation', 'chronicle', 'record', 'inscription', 'craftmanship', 
                        'artisan', 'indigenous', 'tribal', 'ethnography', 'patrimony', 'landmark', 'memorial', 
                        'sanctuary', 'shrine', 'temple', 'cathedral', 'castle', 'fortress', 'ruins', 'settlement', 
                        'civilization', 'dynasty', 'epoch', 'curator', 'geometry', 'cultural', 'heritage', 'historical', 
                        'artifact', 'monument', 'museum', 'exhibition', 'gallery', 'archive', 'library', 'oral history', 
                        'cultural landscape', 'world heritage', 'intangible heritage', 'object','field', 'landscape', 
                        'coverage', 'GIS', 'spatial', 'temporal', 'cartography', 'topography', 'geospatial', 'mapping', 'survey',
                        'remote sensing', 'aerial', 'drone', 'satellite', 'GPS', 'geodesy', 'hydrology', 'geomorphology', 'soil', 
                        'erosion', 'sesimic', 'tectonic', 'volcanic', 'climate', 'vegetation', 'biodiversity', 'ecosystem',
                        'natural', 'environment', 'conservation area', 'protected area', 'national park', 'wildlife']
        matches = sum(1 for word in cultural_words if word in text)
        return min(matches * 0.3, 1.0)
    
    def find_explanations(self, term: str) -> List[TermExplanation]:
        """Find explanations using Wikidata's native search capabilities"""
        
        print(f"🔍 Comprehensive Wikidata search for: '{term}'")
        
        all_results = []
        seen_ids = set()
        
        # 1. Exact search
        print("   📍 Exact search...")
        exact_results = self.search_exact(term)
        for result in exact_results:
            entity_id = result.get('id')
            if entity_id and entity_id not in seen_ids:
                seen_ids.add(entity_id)
                details = self.get_entity_details(entity_id)
                if details.get('label'):
                    details['search_type'] = 'exact'
                    all_results.append(details)
        
        # 2. Fuzzy search using SPARQL
        print("   🔍 Fuzzy search (SPARQL)...")
        fuzzy_results = self.search_fuzzy(term)
        for result in fuzzy_results:
            entity_id = result.get('id')
            if entity_id and entity_id not in seen_ids:
                seen_ids.add(entity_id)
                all_results.append(result)
        
        # 3. Semantic search
        print("   🧠 Semantic search...")
        semantic_results = self.search_semantic(term)
        for result in semantic_results:
            entity_id = result.get('id')
            if entity_id and entity_id not in seen_ids:
                seen_ids.add(entity_id)
                all_results.append(result)
        
        # 4. Full-text search as additional semantic
        print("   📖 Full-text search...")
        fulltext_results = self.search_wikidata_full_text(term)
        for result in fulltext_results:
            entity_id = result.get('id')
            if entity_id and entity_id not in seen_ids:
                seen_ids.add(entity_id)
                all_results.append(result)
        
        # 5. Create TermExplanation objects with relevance assessment
        print("   🤖 LLM relevance assessment...")
        explanations = []
        
        for result in all_results:
            label = result.get('label', '')
            description = result.get('description', '')
            entity_id = result.get('id', '')
            search_type = result.get('search_type', 'unknown')
            
            if label and description:
                relevance_score = self.assess_cultural_heritage_relevance(
                    term, label, description
                )
                
                # Combine label and description for the text field
                combined_text = f"{label}: {description}" if description else label
                
                # Format source according to specified structure
                source_text = f"Wikidata {search_type} search: {entity_id}"
                
                explanations.append(TermExplanation(
                    text=combined_text,
                    score=relevance_score,
                    source=source_text
                ))
        
        # Sort by relevance and return top 3
        explanations.sort(key=lambda x: x.score, reverse=True)
        top_explanations = explanations[:3]
        
        print(f"   ✅ Found {len(top_explanations)} top explanations")
        return top_explanations
    
    def format_for_rag(self, term: str, explanations: List[TermExplanation]) -> str:
        """Format explanations for RAG context"""
        
        if not explanations:
            return f"Term: {term}\nNo relevant explanations found."
        
        rag_text = f"TERM EXPLANATION\n"
        rag_text += f"Term: {term}\n"
        rag_text += f"{'='*40}\n\n"
        
        for i, exp in enumerate(explanations, 1):
            # Parse source to extract components
            source_parts = exp.source.split('\n')
            source_type = source_parts[0] if len(source_parts) > 0 else "unknown"
            entity_id = source_parts[1] if len(source_parts) > 1 else ""
            search_type = source_parts[2] if len(source_parts) > 2 else "unknown"
            
            rag_text += f"{i}. {exp.text}\n"
            rag_text += f"   Relevance Score: {exp.score:.2f}\n"
            rag_text += f"   Search Type: {search_type}\n"
            if entity_id:
                rag_text += f"   Source: https://www.wikidata.org/wiki/{entity_id}\n"
            rag_text += "\n"
        
        return rag_text.strip()
    
    def lookup(self, term: str) -> Dict[str, Any]:
        """Main lookup interface"""
        explanations = self.find_explanations(term)
        
        return {
            'term': term,
            'explanations': explanations,
            'rag_context': self.format_for_rag(term, explanations),
            'count': len(explanations)
        }

def main():
    """Test the native Wikidata search capabilities"""
    
    print("🌐 Wikidata Native Search + LLM Assessment")
    print("=" * 50)
    
    retriever = WikidataNativeSearchRetriever()
    
    test_terms = ["GEOM_LEN", "ZONA"]
    
    for term in test_terms:
        print(f"\n{'='*60}")
        print(f"Testing: {term}")
        print(f"{'='*60}")
        
        try:
            result = retriever.lookup(term)
            print(f"\nFound {result['count']} explanations:")
            
            for i, explanation in enumerate(result['explanations'], 1):
                print(f"\n{i}. TermExplanation:")
                print(f"   text: {explanation.text}")
                print(f"   score: {explanation.score}")
                print(f"   source: {explanation.source}")
            
            print(f"\nRAG Context:\n{result['rag_context']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

# Easy to use:
# retriever = WikidataNativeSearchRetriever()
# result = retriever.lookup(attribute_name)