import json
import math
import pickle
from collections import defaultdict, Counter
from src.crawler.text_processing import preprocess_text


from src.core.config import INDEX_PATH, CLEAN_FILE

class TFIDFIndexer:
   
    def __init__(self):
        self.documents = {}
        self.inverted_index = defaultdict(lambda: defaultdict(list))
        self.tf_index = defaultdict(lambda: defaultdict(int))
        self.idf = {}
        self.doc_vectors = {}
        self.doc_norms = {}
        
    def build_index(self, documents):
        
        self.documents = documents
        N = len(documents)

        print(f"Building index for {N} documents...")

        print("  Building positional index...")
        for doc_id, doc in documents.items():
            tokens = preprocess_text(doc["content"])
            
            for pos, term in enumerate(tokens):
                self.inverted_index[term][doc_id].append(pos)
            
            counts = Counter(tokens)
            for term, freq in counts.items():
                self.tf_index[term][doc_id] = freq

        print("  Computing IDF scores...")
        for term, doc_dict in self.tf_index.items():
            df = len(doc_dict)  # Document frequency
            # Smoothed IDF formula
            self.idf[term] = math.log((N + 1) / (df + 1)) + 1

        print(" Computing TF-IDF vectors...")
        for doc_id, doc in documents.items():
            vector = {}
            norm_sq = 0
            
            for term in self.tf_index.keys():
                tf = self.tf_index[term].get(doc_id, 0)
                if tf > 0:
                    tfidf = tf * self.idf[term]
                    vector[term] = tfidf
                    norm_sq += tfidf ** 2
            
            self.doc_vectors[doc_id] = vector
            self.doc_norms[doc_id] = math.sqrt(norm_sq) if norm_sq > 0 else 0

        print(" Index building complete!")
        return self.get_index_dict()
    
    def get_index_dict(self):
        return {
            "documents": self.documents,
            "inverted_index": dict(self.inverted_index),
            "tf_index": dict(self.tf_index),
            "idf": self.idf,
            "doc_vectors": self.doc_vectors,
            "doc_norms": self.doc_norms
        }
    
    def save_index(self, filepath=INDEX_PATH):
        # Convert defaultdicts to regular dicts for pickling
        index_data = self._convert_to_regular_dicts(self.get_index_dict())
        
        with open(filepath, "wb") as f:
            pickle.dump(index_data, f)
        
        print(f" Index saved to {filepath}")
        
        # Print statistics
        self.print_statistics()
    
    @staticmethod
    def _convert_to_regular_dicts(obj):
        if isinstance(obj, defaultdict):
            obj = {k: TFIDFIndexer._convert_to_regular_dicts(v) 
                   for k, v in obj.items()}
        elif isinstance(obj, dict):
            obj = {k: TFIDFIndexer._convert_to_regular_dicts(v) 
                   for k, v in obj.items()}
        return obj
    
    @staticmethod
    def load_index(filepath=INDEX_PATH):
        with open(filepath, "rb") as f:
            index = pickle.load(f)
        print(f" Index loaded from {filepath}")
        return index
    
    def print_statistics(self):
        print("\n Index Statistics:")
        print(f"  Documents: {len(self.documents)}")
        print(f"  Unique terms: {len(self.inverted_index)}")
        print(f"  Total postings: {sum(len(docs) for docs in self.inverted_index.values())}")
        
        if self.doc_norms:
            avg_norm = sum(self.doc_norms.values()) / len(self.doc_norms)
            print(f"  Average doc vector norm: {avg_norm:.2f}")


def build_index_from_file(input_file=CLEAN_FILE, 
                           output_file=INDEX_PATH):
    # Load documents
    with open(input_file, "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    # Build index
    indexer = TFIDFIndexer()
    indexer.build_index(documents)
    
    # Save index
    indexer.save_index(output_file)


if __name__ == "__main__":
    build_index_from_file()