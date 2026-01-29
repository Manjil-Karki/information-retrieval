from src.services.search_engine import SearchEngine

from src.core.config import INDEX_PATH
_search_engine = None


def get_search_engine(index_path=INDEX_PATH):

    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine(index_path)
    return _search_engine


def search_publications(query, top_n=5, index_path=INDEX_PATH):

    engine = get_search_engine(index_path)
    results = engine.search(query, top_n=top_n)
    
    # Convert to API-friendly format
    return [
        {
            "doc_id": doc_id,
            "score": float(score),
            "title": doc["title"],
            "year": doc.get("year"),
            "authors": [
                {
                    "name": author["name"],
                    "profile_url": author.get("profile_url")
                }
                for author in doc.get("authors", [])
            ],
            "journal": doc.get("journal", ""),
            "type": doc.get("type", ""),
            "citations": doc.get("citations", "0"),
            "altmetric_score": doc.get("altmetric_score", "0"),
            "concepts": doc.get("concepts", []),
            "url": doc.get("publication_url", ""),
            "doi": doc.get("doi", "")
        }
        for doc_id, score, doc in results
    ]


def get_document_by_id(doc_id, index_path=INDEX_PATH):

    engine = get_search_engine(index_path)
    
    if doc_id in engine.documents:
        doc = engine.documents[doc_id]
        return {
            "doc_id": doc_id,
            "title": doc["title"],
            "year": doc.get("year"),
            "authors": doc.get("authors", []),
            "journal": doc.get("journal", ""),
            "volume": doc.get("volume", ""),
            "type": doc.get("type", ""),
            "citations": doc.get("citations", "0"),
            "altmetric_score": doc.get("altmetric_score", "0"),
            "concepts": doc.get("concepts", []),
            "url": doc.get("publication_url", ""),
            "doi": doc.get("doi", "")
        }
    return None


def get_index_statistics(index_path=INDEX_PATH):
    engine = get_search_engine(index_path)
    return engine.get_statistics()


# Example usage for testing
if __name__ == "__main__":
    # Test search
    print("Testing search_publications():")
    results = search_publications("machine learning", top_n=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. [{result['score']:.4f}] {result['title']}")
        print(f"   Authors: {', '.join([a['name'] for a in result['authors'][:3]])}")
        print(f"   Year: {result['year']}")
    
    

    # Test document retrieval
    print("\nTesting get_document_by_id():")
    if results:
        doc_id = results[0]['doc_id']
        doc = get_document_by_id(doc_id)
        print(f"Retrieved: {doc['title']}")
    
    print("\n" + "="*80)
    
    # Test statistics
    print("\nTesting get_index_statistics():")
    stats = get_index_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")