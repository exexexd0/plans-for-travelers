"""Единая предобработка документов и запросов с русской лемматизацией."""

import re
import unicodedata

from pymorphy3 import MorphAnalyzer

_WORDS = re.compile(r"[^\W_]+", re.UNICODE)
_MORPH = MorphAnalyzer(lang="ru")
_STOP_WORDS = frozenset({
    "а", "бы", "в", "во", "для", "до", "же", "за", "и", "из", "или",
    "к", "ко", "как", "на", "над", "но", "о", "об", "от", "по", "под",
    "при", "про", "с", "со", "то", "у", "через", "что", "чтобы", "это",
})


def preprocess(text: str) -> list[str]:
    if not isinstance(text, str):
        raise TypeError("Текст должен быть строкой")
    normalized = unicodedata.normalize("NFKC", text).casefold()
    tokens = _WORDS.findall(normalized)
    lemmas = [
        _MORPH.parse(token)[0].normal_form if token.isalpha() else token
        for token in tokens
    ]
    return [lemma for lemma in lemmas if lemma not in _STOP_WORDS]
