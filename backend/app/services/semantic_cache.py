import json
import numpy as np
from fastembed import TextEmbedding
import redis

class SemanticCache:
    def __init__(self, redis_url: str = "redis://redis:6379", threshold: float = 0.90):
        self.client = redis.from_url(redis_url)
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.threshold = threshold

    def _get_embedding(self, text: str) -> list[float]:
        return list(self.embedder.embed([text]))[0].tolist()

    def get(self, query: str) -> dict | None:
        query_vec = np.array(self._get_embedding(query), dtype=np.float32)
        keys = self.client.keys("cache:draft:*")
        
        best_score = -1.0
        best_data = None
        
        for key in keys:
            entry = json.loads(self.client.get(key))
            stored_vec = np.array(entry["vector"], dtype=np.float32)
            # Cosine similarity ගණනය කිරීම
            similarity = np.dot(query_vec, stored_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(stored_vec))
            
            if similarity > best_score:
                best_score = similarity
                best_data = entry["data"]
                
        if best_score >= self.threshold:
            return best_data
        return None

    def set(self, query: str, data: dict, ttl_seconds: int = 86400):
        vector = self._get_embedding(query)
        payload = {
            "query": query,
            "vector": vector,
            "data": data,
        }
        key = f"cache:draft:{hash(query)}"
        self.client.setex(key, ttl_seconds, json.dumps(payload))