import json
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Hit:
    id: str
    title: str
    answer: str
    score: float


class FaqRetriever:
    """TF-IDF (char n-grams, so typos like 'refnd' still match) over the FAQ file."""

    def __init__(self, path: str) -> None:
        self.entries = json.loads(Path(path).read_text(encoding="utf-8"))
        docs = [f'{e["title"]}. {e["question"]} {e["answer"]}' for e in self.entries]
        self._vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        self._m = self._vec.fit_transform(docs)

    def search(self, text: str, k: int = 3) -> list[Hit]:
        sims = cosine_similarity(self._vec.transform([text]), self._m)[0]
        order = sims.argsort()[::-1][:k]
        return [Hit(self.entries[i]["id"], self.entries[i]["title"], self.entries[i]["answer"], float(sims[i]))
                for i in order]
