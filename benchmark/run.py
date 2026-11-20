"""Простой поисковый benchmark: python -m benchmark.run из корня проекта."""

import json
from pathlib import Path

from app.backend.infrastructure.corpus.loader import load_places
from app.backend.infrastructure.search.bm25 import BM25Search

ROOT = Path(__file__).resolve().parents[1]
K = 3


def main():
    # 1. Загружаем документы, строим индекс и читаем вопросы.
    places = load_places(ROOT / "app/backend/data/ivanovo")
    index = BM25Search(places, k1=1.2, b=0.75)
    questions = json.loads((ROOT / "benchmark/questions.json").read_text(encoding="utf-8"))
    results = []
    recall_sum = 0.0
    rr_sum = 0.0
    ordinary_count = 0

    # 2. Находим три документа для каждого вопроса.
    for question in questions:
        hits = index.search(question["question"], city="Иваново", limit=K)
        found_ids = [hit.place.id for hit in hits]
        recall = None
        rr = None

        # 3. Считаем метрики только для обычных вопросов.
        if question["type"] == "answerable":
            relevant = set(question["relevant_ids"])
            recall = len(set(found_ids) & relevant) / len(relevant)
            rr = 0.0
            for rank, id in enumerate(found_ids, start=1):
                if id in relevant:
                    rr = 1 / rank
                    break
            recall_sum += recall
            rr_sum += rr
            ordinary_count += 1

        results.append({
            "id": question["id"], "type": question["type"], "question": question["question"],
            "relevant_ids": question["relevant_ids"], "reference_answer": question["reference_answer"],
            "hits": [{"id": hit.place.id, "name": hit.place.name, "score": hit.score,
                      "places": [{"id": p.id, "name": p.name, "address": p.address,
                                  "lat": p.lat, "lon": p.lon, "source": p.source}
                                 for p in hit.place.places]} for hit in hits],
            "recall_at_3": recall, "rr_at_3": rr,
        })

    # 4. Усредняем по обычным вопросам и сохраняем результат.
    recall = recall_sum / ordinary_count
    mrr = rr_sum / ordinary_count
    report = {"k": K, "k1": 1.2, "b": 0.75, "documents": len(places),
              "ordinary_questions": ordinary_count, "trap_questions": len(questions) - ordinary_count,
              "metrics": {"Recall@3": recall, "MRR@3": mrr}, "results": results}
    output = ROOT / "benchmark/results"
    output.mkdir(exist_ok=True)
    (output / "search.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Та же выдача в таблице для ручной проверки.
    lines = ["# Поисковый benchmark", "", f"Документов: {len(places)}; обычных вопросов: {ordinary_count}; ловушек: {len(questions) - ordinary_count}.",
             "k = 3, k₁ = 1,2, b = 0,75.", "", f"Recall@3: {recall:.6f}", f"MRR@3: {mrr:.6f}", "",
             "LLM не вызывалась. Accuracy и Correct Rejection Rate пока не вычислены.",
             "Ловушки не входят в Recall@3 и MRR@3. Эталоны и ошибки проверяем вручную.", "",
             "| Вопрос | Найденные места: ID и балл | Recall@3 | RR@3 |", "|---|---|---:|---:|"]
    for result in results:
        found = "; ".join(f"{h['name']} ({h['id']}, {h['score']:.3f}; мест: {len(h['places'])})" for h in result["hits"]) or "Нет совпадений"
        r = "—" if result["recall_at_3"] is None else f"{result['recall_at_3']:.4f}"
        rr = "—" if result["rr_at_3"] is None else f"{result['rr_at_3']:.4f}"
        lines.append(f"| {result['id']} | {found} | {r} | {rr} |")
    (output / "search.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Recall@3: {recall:.6f}\nMRR@3: {mrr:.6f}\nРезультаты: benchmark/results/search.json и search.md")


if __name__ == "__main__":
    main()
