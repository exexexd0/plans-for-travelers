"""Изолированный консольный поиск без сервера и LLM."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from app.backend.infrastructure.corpus.loader import load_places
from app.backend.infrastructure.search.bm25 import BM25Search


def main() -> None:
    parser = argparse.ArgumentParser(description="Собственный BM25: поиск по JSON-корпусу")
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--city")
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--exclude-id", action="append", default=[])
    parser.add_argument("--k1", type=float, default=1.2)
    parser.add_argument("--b", type=float, default=0.75)
    args = parser.parse_args()
    try:
        index = BM25Search(load_places(args.corpus), k1=args.k1, b=args.b)
        hits = index.search(
            args.query, city=args.city, limit=args.limit,
            categories=args.category, excluded_ids=args.exclude_id,
        )
    except (OSError, ValueError, TypeError) as error:
        parser.error(str(error))
    print(json.dumps({
        "query": args.query,
        "document_count": index.document_count,
        "average_document_length": index.average_document_length,
        "k1": args.k1, "b": args.b, "limit": args.limit,
        "results": [asdict(hit) for hit in hits],
    }, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
