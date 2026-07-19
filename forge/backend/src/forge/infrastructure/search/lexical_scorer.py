"""Lexical scorer for fallback hybrid search."""
import math
from collections import Counter

class LocalLexicalScorer:
    """Simple BM25-like lexical scorer for fallback hybrid search."""
    
    def score(self, query: str, documents: list[str]) -> list[float]:
        """Score a list of documents against a query."""
        if not documents:
            return []
        import re
        def tokenize(text: str) -> list[str]:
            text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
            text = text.replace('_', ' ')
            return re.findall(r'[a-zA-Z0-9]+', text.lower())

        q_terms = set(tokenize(query))
        doc_terms = [tokenize(doc) for doc in documents]
        
        # Calculate IDF
        N = len(documents)
        df = Counter()
        for d_terms in doc_terms:
            for term in set(d_terms):
                df[term] += 1
                
        idf = {}
        for term in q_terms:
            # Add 1 smoothing
            idf[term] = math.log((N - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5) + 1.0)
            
        scores = []
        avgdl = sum(len(d) for d in doc_terms) / N
        k1 = 1.5
        b = 0.75
        
        for d_terms in doc_terms:
            d_count = Counter(d_terms)
            score = 0.0
            dl = len(d_terms)
            for term in q_terms:
                if term in d_count:
                    tf = d_count[term]
                    score += idf[term] * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
            scores.append(score)
            
        return scores
