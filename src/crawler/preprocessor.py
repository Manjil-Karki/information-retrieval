import json
import re
from pathlib import Path

from src.core.config import DATA_JSON, PROCESSED_DOCUMENTS


class PublicationPreprocessor:
    
    def __init__(self, input_file=None):
        self.input_file = input_file or DATA_JSON
        self.processed_publications = {}
        self.doc_counter = 1
        
    @staticmethod
    def extract_year(date_str):
        if not date_str:
            return None
        match = re.search(r"\b(19|20)\d{2}\b", date_str)
        return int(match.group()) if match else None

    @staticmethod
    def preprocess_text(text):
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        tokens = text.split()
        return " ".join(tokens)
    
    @staticmethod
    def format_author_name(name):
        parts = name.split()
        if len(parts) == 0:
            return name
        
        if len(parts) == 1:
            return parts[0]
        
        last_name = parts[-1]
        initials = [p[0].upper() + "." for p in parts[:-1] if p]
        
        return f"{last_name}, {' '.join(initials)}"

    def process(self):
        input_path = Path(self.input_file)
        
        if not input_path.exists():
            print(f"Error: Input file not found: {self.input_file}")
            return {}
        
        with open(input_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        publications = raw_data.get("publications", {})

        for pub_url, pub_data in publications.items():
            doc_id = f"DOC_{self.doc_counter:04d}"
            
            authors_list = []
            for author in pub_data.get("authors", []):
                author_name = author.get("name", "")
                author_url = author.get("url")
                
                formatted_name = self.format_author_name(author_name)
                
                authors_list.append({
                    "name": formatted_name,
                    "profile_url": author_url
                })
            
            title = pub_data.get("title", "")
            abstract = pub_data.get("abstract", "")
            
            publication_date = pub_data.get("publication_date", "")
            year = self.extract_year(publication_date)
            
            citations = pub_data.get("citations_scopus")
            if citations is None:
                citations = 0
            
            doi = pub_data.get("doi", "")
            
            self.processed_publications[doc_id] = {
                "title": title,
                "year": year,
                "authors": authors_list,
                "publication_url": pub_url,
                "journal": pub_data.get("journal", ""),
                "volume": pub_data.get("volume", ""),
                "pages": pub_data.get("pages", ""),
                "doi": doi,
                "citations": citations,
                "abstract": abstract,
                "content": self.preprocess_text(title + " " + abstract),
            }
            self.doc_counter += 1

        return self.processed_publications

    def save(self, output_file=None):
        if not self.processed_publications:
            self.process()
        
        output_path = output_file or PROCESSED_DOCUMENTS
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.processed_publications, f, indent=2, ensure_ascii=False)

        print(f"Processed {len(self.processed_publications)} unique publications.")
        print(f"Data saved to {output_path}")


if __name__ == "__main__":
    preprocessor = PublicationPreprocessor()
    preprocessor.save()