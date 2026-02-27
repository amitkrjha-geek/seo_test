"""
NLP text analysis module.

Provides readability scoring (via textstat) and keyword density
analysis using simple tokenisation (no spaCy dependency).
"""

import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

_STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on",
    "at", "to", "for", "of", "with", "by", "from", "as",
    "is", "was", "are", "were", "been", "be", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "must", "it", "its",
    "i", "me", "my", "we", "our", "you", "your", "he",
    "him", "his", "she", "her", "they", "them", "their", "this",
    "that", "these", "those", "which", "who", "whom", "what", "when",
    "where", "why", "how", "all", "each", "every", "both", "few",
    "more", "most", "other", "some", "such", "no", "not", "only",
    "same", "so", "than", "too", "very", "just", "about", "above",
    "after", "again", "also", "am", "any", "because", "before", "being",
    "below", "between", "during", "here", "if", "into", "out", "over",
    "own", "then", "there", "through", "under", "until", "up", "while",
    "s", "t", "re", "ve", "ll", "d", "m", "don",
    "doesn", "didn", "wasn", "weren", "won", "wouldn", "couldn", "shouldn",
    "hasn", "haven", "hadn", "isn", "aren", "ain", "nor", "get",
    "got", "us", "much",
}


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokeniser. Returns lowercased tokens."""
    text = text.lower()
    text = re.sub(r"'s\b", "", text)
    tokens = re.findall(r"\b[a-z][a-z\-]*[a-z]\b|\b[a-z]\b", text)
    return tokens


def _sentences(text: str) -> list[str]:
    """Split text into sentences using a simple regex heuristic."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if s.strip()]


def _compute_keyword_density(tokens: list[str], top_n: int = 20) -> list[dict]:
    """Return the top N keywords by frequency, excluding stop-words."""
    filtered = [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]
    if not filtered:
        return []
    total = len(filtered)
    counter = Counter(filtered)
    return [
        {
            "keyword": word,
            "count": count,
            "density_percent": round((count / total) * 100, 2),
        }
        for word, count in counter.most_common(top_n)
    ]


def analyze_text(text: str) -> dict:
    """
    Perform NLP analysis on the given text.

    Parameters
    ----------
    text:
        Plain text (typically the visible text extracted from a web page).

    Returns
    -------
    dict with keys:
        readability_score   - Flesch Reading Ease (0-100+, higher = easier)
        grade_level         - Flesch-Kincaid Grade Level
        word_count          - total number of words
        sentence_count      - total number of sentences
        avg_sentence_length - average words per sentence
        keyword_density     - list of top 20 keywords with count and density pct
    """
    result: dict = {
        "readability_score": None,
        "grade_level": None,
        "word_count": 0,
        "sentence_count": 0,
        "avg_sentence_length": 0.0,
        "keyword_density": [],
    }
    if not text or not text.strip():
        return result

    tokens = _tokenize(text)
    sentences = _sentences(text)
    word_count = len(tokens)
    sentence_count = len(sentences)

    result["word_count"] = word_count
    result["sentence_count"] = sentence_count
    result["avg_sentence_length"] = (
        round(word_count / sentence_count, 1) if sentence_count > 0 else 0.0
    )

    # Readability via textstat (optional dependency)
    try:
        import textstat
        result["readability_score"] = textstat.flesch_reading_ease(text)
        result["grade_level"] = textstat.flesch_kincaid_grade(text)
    except ImportError:
        logger.warning(
            "textstat is not installed -- readability metrics will be None. "
            "Install with: pip install textstat"
        )
    except Exception as exc:
        logger.error("textstat error: %s", exc)

    # Keyword density
    try:
        result["keyword_density"] = _compute_keyword_density(tokens, top_n=20)
    except Exception as exc:
        logger.error("Keyword density calculation failed: %s", exc)

    return result
