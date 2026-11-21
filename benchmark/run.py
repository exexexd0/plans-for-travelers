"""Только BM25: python -m benchmark.run [--k 3] [--question Q01]."""

import argparse
import json
from pathlib import Path

from app.backend.infrastructure.corpus.loader import load_places
from app.backend.infrastructure.search.bm25 import BM25Search

ROOT = Path(__file__).resolve().parents[1]


def evaluate(found_ids, relevant_ids):
    relevant = set(relevant_ids)
    if not relevant:
        raise ValueError("Для оценки обычного вопроса нужны relevant_ids")
    recall = len(set(found_ids) & relevant) / len(relevant)
    rr = next((1 / rank for rank, id in enumerate(found_ids, 1) if id in relevant), 0.0)
    return recall, rr


def run_benchmark(index, questions, k):
    results = []
    for q in questions:
        # Эталоны и категории не передаются поиску.
        hits = index.search(q["question"], city=q.get("city", "Иваново"), limit=k)
        found = [hit.place.id for hit in hits]
        recall, rr = None, None
        if q["type"] == "answerable":
            recall, rr = evaluate(found, q["relevant_ids"])
        results.append({"id": q["id"], "type": q["type"], "question": q["question"],
                        "city": q.get("city", "Иваново"), "relevant_ids": q["relevant_ids"],
                        "hits": [{"id": h.place.id, "name": h.place.name, "score": h.score} for h in hits],
                        "recall_at_k": recall, "rr_at_k": rr})
    ordinary = [r for r in results if r["type"] == "answerable"]
    return {"k": k, "documents": index.document_count, "k1": 1.2, "b": 0.75,
            "ordinary_questions": len(ordinary), "unanswerable_questions": len(results) - len(ordinary),
            "metrics": {f"Recall@{k}": sum(r["recall_at_k"] for r in ordinary) / len(ordinary) if ordinary else None,
                        f"MRR@{k}": sum(r["rr_at_k"] for r in ordinary) / len(ordinary) if ordinary else None},
            "results": results}


def save_report(report, output):
    output.mkdir(exist_ok=True)
    (output / "bm25.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    k = report["k"]
    lines = ["# Benchmark BM25", "", f"Документов: {report['documents']}; k = {k}.",
             "Один полный вопрос → одна выдача, без фильтрации по категориям.",
             "LLM, планировщик, JEV и OSRM не вызываются.", "",
             f"Обычных вопросов: {report['ordinary_questions']}; без подтверждённого ответа: {report['unanswerable_questions']}.", "",
             "| Метрика | Значение |", "|---|---:|"]
    for name, value in report["metrics"].items():
        lines.append(f"| {name} | {value:.6f} |" if value is not None else f"| {name} | Нет обычных вопросов |")
    lines += ["", "Recall@k = найденные релевантные ID / все релевантные ID вопроса.",
              "RR@k = 1 / позиция первого релевантного ID либо 0; MRR@k — среднее RR@k.",
              "Обе метрики усредняются только по обычным вопросам. Для пяти вопросов без ответа сохраняется выдача, но метрики не считаются.",
              "Правильность маршрутов и отказы BM25 не оценивает. Текущий набор содержит широкие категории и перефразировки; результат относится только к этому набору.", ""]
    for r in report["results"]:
        lines += [f"## {r['id']}", "", "> " + r["question"], "",
                  "Релевантные документы: " + (", ".join(r["relevant_ids"]) or "нет") + ".", "",
                  "BM25: " + (", ".join(f"{h['id']} ({h['score']:.4f})" for h in r["hits"]) or "совпадений нет") + ".", ""]
        if r["recall_at_k"] is not None:
            found = {h["id"] for h in r["hits"]}
            relevant = set(r["relevant_ids"])
            lines += [f"Recall@{k} = {len(found & relevant)} / {len(relevant)} = {r['recall_at_k']:.6f}; RR@{k} = {r['rr_at_k']:.6f}.", ""]
        else:
            lines += ["В метрики поиска не входит.", ""]
    (output / "bm25.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, help="Лимит выдачи и глубина MRR; по умолчанию весь корпус")
    parser.add_argument("--question", choices=[f"Q{i:02}" for i in range(1, 16)])
    args = parser.parse_args()
    if args.k is not None and args.k <= 0:
        parser.error("k должен быть положительным")
    documents = load_places(ROOT / "app/backend/data/ivanovo")
    index = BM25Search(documents, k1=1.2, b=0.75)
    questions = json.loads((ROOT / "benchmark/questions.json").read_text(encoding="utf-8"))
    if args.question:
        questions = [q for q in questions if q["id"] == args.question]
    k = args.k if args.k is not None else index.document_count
    report = run_benchmark(index, questions, k)
    save_report(report, ROOT / "benchmark/results")
    for name, value in report["metrics"].items():
        print(f"{name}: {value:.6f}" if value is not None else f"{name}: нет обычных вопросов")
    print("Результаты: benchmark/results/bm25.json и bm25.md")


if __name__ == "__main__":
    main()
