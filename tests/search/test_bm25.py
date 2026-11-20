"""Формула занятия 3, поведение поиска и предобработка."""

from math import log
import unittest

from app.backend.domain.models import Place
from app.backend.infrastructure.search.bm25 import BM25Search
from app.backend.infrastructure.search.preprocessing import preprocess


def document(id: str, text: str, **kwargs) -> Place:
    return Place(id=id, name=id, city=kwargs.pop("city", "Учебный пример"), text=text, **kwargs)


class PreprocessingTests(unittest.TestCase):
    def test_unicode_words_and_separators(self):
        self.assertEqual(preprocess("ЁЖИК, парк-музей_2! ＡBC"), ["ёжик", "парк", "музей", "2", "abc"])

    def test_lemmatization_preserves_repetitions(self):
        self.assertEqual(preprocess("Музей музея и музей"), ["музей", "музей", "музей"])

    def test_stopwords_removed_and_negations_preserved(self):
        self.assertEqual(preprocess("в из и по для через"), [])
        self.assertEqual(preprocess("не нет ни без"), ["не", "нет", "ни", "без"])

    def test_different_russian_forms_have_the_same_lemma(self):
        self.assertEqual(preprocess("музей музеи музеях"), ["музей"] * 3)
        self.assertEqual(preprocess("театры театрах театром"), ["театр"] * 3)

    def test_numbers_and_mixed_identifiers_are_preserved(self):
        self.assertEqual(preprocess("А113 2026 17"), ["а113", "2026", "17"])

    def test_empty_and_punctuation(self):
        for text in ("", "   ", "!?_—"):
            self.assertEqual(preprocess(text), [])

    def test_text_is_required(self):
        with self.assertRaises(TypeError):
            preprocess(None)


class BM25Tests(unittest.TestCase):
    def setUp(self):
        self.index = BM25Search([
            document("C", "Возврат билета через кассу."),
            document("B", "Статус оплаты в приложении."),
            document("A", "Возврат оплаты на карту."),
        ])

    def test_exact_presentation_scores_and_order(self):
        hits = self.index.search("Как происходит возврат оплаты?", city=None, limit=3)
        self.assertEqual([h.place.id for h in hits], ["A", "B", "C"])
        self.assertAlmostEqual(hits[0].score, 0.9400072584914713)
        self.assertAlmostEqual(hits[1].score, 0.47000362924573563)
        self.assertAlmostEqual(hits[2].score, 0.47000362924573563)
        self.assertEqual(self.index.document_count, 3)
        self.assertEqual(self.index.average_document_length, 3)

    def test_inflected_query_matches_document(self):
        index = BM25Search([document("A", "музей"), document("B", "кафе")])
        hits = index.search("музеях", city=None, limit=2)
        self.assertEqual([h.place.id for h in hits], ["A"])
        self.assertEqual(hits, index.search("музей", city=None, limit=2))

    def test_document_inflections_merge_into_term_frequency(self):
        index = BM25Search([
            document("A", "музей музеи музеях"),
            document("B", "музей музей музей"),
        ])
        hits = index.search("музеями", city=None, limit=2)
        self.assertEqual([h.place.id for h in hits], ["A", "B"])
        self.assertEqual(hits[0].score, hits[1].score)
        self.assertEqual(index.search("музеи музеях", city=None, limit=2), hits)

    def test_presentation_top_two(self):
        hits = self.index.search("Как происходит возврат оплаты?", city=None, limit=2)
        self.assertEqual([h.place.id for h in hits], ["A", "B"])

    def test_query_preprocessing_and_duplicates(self):
        expected = self.index.search("возврат оплаты", city=None, limit=3)
        self.assertEqual(self.index.search("ВОЗВРАТ, оплаты! возврат", city=None, limit=3), expected)
        self.assertEqual(self.index.search("возврат оплаты неизвестное", city=None, limit=3), expected)

    def test_only_matching_documents_are_returned(self):
        self.assertEqual([h.place.id for h in self.index.search("кассу", city=None, limit=20)], ["C"])
        for query in ("", "  ", "???", "несуществующее"):
            self.assertEqual(self.index.search(query, city=None, limit=2), [])

    def test_tf_saturates_at_equal_lengths(self):
        index = BM25Search([
            document("A", "парк сад сад"), document("B", "парк парк сад"),
            document("C", "парк парк парк"),
        ])
        scores = {h.place.id:h.score for h in index.search("парк",city=None,limit=3)}
        self.assertAlmostEqual(scores["B"]/scores["A"], 1.375)
        self.assertGreater(scores["B"]-scores["A"], scores["C"]-scores["B"])

    def test_length_normalization_and_b_zero(self):
        docs = [document("A", "парк сад сад сад"),document("B", "парк")]
        normalized = BM25Search(docs,b=1).search("парк",city=None,limit=2)
        self.assertEqual([h.place.id for h in normalized],["B","A"])
        unnormalized = BM25Search(docs,b=0).search("парк",city=None,limit=2)
        self.assertEqual([h.place.id for h in unnormalized],["A","B"])
        self.assertEqual(unnormalized[0].score,unnormalized[1].score)

    def test_rare_term_contributes_more(self):
        index=BM25Search([document("A","музей парк"),document("B","парк сад"),document("C","парк сад")])
        rare=index.search("музей",city=None,limit=1)[0].score
        common=index.search("парк",city=None,limit=1)[0].score
        self.assertGreater(rare,common)

    def test_empty_corpus_and_empty_documents(self):
        for docs in ([],[document("A","")],[document("A","!!!")]):
            self.assertEqual(BM25Search(docs).search("парк",city=None,limit=2),[])
        index=BM25Search([document("A","парк"),document("B","")])
        self.assertEqual(index.document_count,2)
        self.assertEqual(index.average_document_length,0.5)
        self.assertEqual([h.place.id for h in index.search("парк",city=None,limit=3)],["A"])

    def test_filters_apply_before_limit_and_do_not_change_statistics(self):
        index=BM25Search([
            document("A","парк",city="Иваново",category="природа"),
            document("B","парк",city="Казань",category="природа"),
            document("C","парк",city="Иваново",category="музей"),
            document("D","парк",city="Иваново",category="природа"),
        ])
        all_hits=index.search("парк",city=None,limit=4)
        hits=index.search("парк",city=" ИВАНОВО ",limit=1,categories=("природа",),excluded_ids=("A",))
        self.assertEqual([h.place.id for h in hits],["D"])
        self.assertEqual(hits[0].score,all_hits[0].score)
        self.assertEqual(index.search("парк",city="нет такого города",limit=1),[])
        self.assertEqual(index.search("парк",city=None,limit=1,categories=("нет",)),[])

    def test_duplicate_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"Повтор ID"):
            BM25Search([document("A","один"),document("A","два")])

    def test_parameters_are_validated(self):
        for kwargs in ({"k1":0},{"k1":-1},{"k1":float("nan")},{"k1":float("inf")},{"b":-0.1},{"b":1.1},{"b":True},{"k1":"1.2"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                BM25Search([],**kwargs)

    def test_limit_is_validated(self):
        for limit in (0,-1,True,1.5):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.index.search("возврат",city=None,limit=limit)

    def test_single_document_idf_is_positive(self):
        hit=BM25Search([document("A","парк")]).search("парк",city=None,limit=1)[0]
        self.assertAlmostEqual(hit.score,log(4/3))


if __name__ == "__main__":
    unittest.main()
