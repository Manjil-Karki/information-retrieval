import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize


class TextProcessor:
    def __init__(self):
        self._download_nltk_resources()
        self.stop_words = set(stopwords.words("english"))
        self.stemmer = PorterStemmer()
    
    @staticmethod
    def _download_nltk_resources():
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("Downloading NLTK punkt tokenizer...")
            nltk.download("punkt", quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            print("Downloading NLTK stopwords...")
            nltk.download("stopwords", quiet=True)
    
    def preprocess_text(self, text):
        # Lowercasing
        text = text.lower()
        
        # Remove non-alphanumeric characters
        text = re.sub(r"[^a-z0-9\s]", "", text)

        # Tokenization
        tokens = word_tokenize(text)

        # Stopword removal and stemming
        processed = [
            self.stemmer.stem(token)
            for token in tokens
            if token not in self.stop_words
        ]

        return processed
    
    def preprocess_query(self, query):
        return self.preprocess_text(query)


# Singleton instance for convenient import
_processor = None

def get_processor():
    global _processor
    if _processor is None:
        _processor = TextProcessor()
    return _processor


def preprocess_text(text):
    return get_processor().preprocess_text(text)


if __name__ == "__main__":
    # Example usage
    processor = TextProcessor()
    
    sample_text = "Machine Learning and Artificial Intelligence are transforming healthcare!"
    processed = processor.preprocess_text(sample_text)
    
    print(f"Original: {sample_text}")
    print(f"Processed: {processed}")