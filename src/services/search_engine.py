import math
import pickle
from collections import Counter
from src.crawler.text_processing import preprocess_text

from src.core.config import INDEX_PATH

class SearchEngine:
    
    def __init__(self, index_path=INDEX_PATH):
        self.index = self._load_index(index_path)
        self.documents = self.index["documents"]
        self.doc_vectors = self.index["doc_vectors"]
        self.doc_norms = self.index["doc_norms"]
        self.idf = self.index["idf"]
        
        print(f" Search engine initialized with {len(self.documents)} documents")
    
    @staticmethod
    def _load_index(index_path):
        with open(index_path, "rb") as f:
            index = pickle.load(f)
        return index
    
    @staticmethod
    def cosine_similarity(query_vec, doc_vec, doc_norm):
        
        # Dot product
        dot_product = sum(
            query_vec.get(term, 0) * weight 
            for term, weight in doc_vec.items()
        )
        

        query_norm = math.sqrt(sum(v ** 2 for v in query_vec.values()))
        

        if query_norm == 0 or doc_norm == 0:
            return 0.0
        

        return dot_product / (query_norm * doc_norm)
    
    def build_query_vector(self, query_terms):
        
        query_counts = Counter(query_terms)
        
        # Build TF-IDF vector using index IDF scores
        query_vec = {
            term: freq * self.idf.get(term, 0) 
            for term, freq in query_counts.items()
        }
        
        return query_vec
    
    def search(self, query, top_n=5):
        
        query_terms = preprocess_text(query)
        
        if not query_terms:
            print(" Query produced no valid terms after preprocessing")
            return []
        
        # Build query vector
        query_vec = self.build_query_vector(query_terms)
        
        scores = []
        for doc_id, doc_vec in self.doc_vectors.items():
            similarity = self.cosine_similarity(
                query_vec, 
                doc_vec, 
                self.doc_norms[doc_id]
            )
            
            if similarity > 0:  
                scores.append((similarity, doc_id))

        scores.sort(reverse=True)
        
        # Prepare results
        results = [
            (doc_id, score, self.documents[doc_id]) 
            for score, doc_id in scores[:top_n]
        ]
        
        return results
    
    def format_results(self, results, show_full=False):
        if not results:
            return "No results found."
        
        output = [f"\n🔍 Found {len(results)} results:\n"]
        
        for i, (doc_id, score, doc) in enumerate(results, 1):
            output.append(f"\n{'='*80}")
            output.append(f"Rank {i} | Score: {score:.4f} | Doc ID: {doc_id}")
            output.append(f"{'='*80}")
            output.append(f"Title: {doc['title']}")
            
            if show_full:
                # Authors
                authors = doc.get('authors', [])
                if authors:
                    author_names = [a['name'] for a in authors if a.get('name')]
                    output.append(f"Authors: {', '.join(author_names)}")
                
                # Publication details
                if doc.get('year'):
                    output.append(f"Year: {doc['year']}")
                if doc.get('journal'):
                    output.append(f"Journal: {doc['journal']}")
                if doc.get('type'):
                    output.append(f"Type: {doc['type']}")
                
                # Metrics
                citations = doc.get('citations', '0')
                altmetric = doc.get('altmetric_score', '0')
                output.append(f"Citations: {citations} | Altmetric: {altmetric}")
                
                # Concepts
                concepts = doc.get('concepts', [])
                if concepts:
                    output.append(f"Concepts: {', '.join(concepts)}")
                
                # URL
                if doc.get('publication_url'):
                    output.append(f"URL: {doc['publication_url']}")
        
        return '\n'.join(output)
    
    def get_statistics(self):
        return {
            "total_documents": len(self.documents),
            "total_terms": len(self.idf),
            "avg_doc_length": sum(
                len(preprocess_text(doc["content"])) 
                for doc in self.documents.values()
            ) / len(self.documents) if self.documents else 0
        }

