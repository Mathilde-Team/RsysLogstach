"""Tests pytest pour fingerprint.py::compute_fingerprint (session 17).

Couvre l'empreinte du document entier (fields=None/[]), l'empreinte d'une
sélection ordonnée de champs (y compris imbriqués), le repli sur `None`
quand tous les champs demandés sont absents, la sélection de l'algorithme
de hachage, et l'erreur sur une méthode inconnue.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from fingerprint import compute_fingerprint


class TestWholeDocumentFingerprint:
    """`fields=None` ou `fields=[]` : hash du document entier (JSON canonique)."""

    def test_none_and_empty_list_produce_same_result(self) -> None:
        doc = {"b": 2, "a": 1}
        assert compute_fingerprint(doc, None) == compute_fingerprint(doc, [])

    def test_key_insertion_order_does_not_matter(self) -> None:
        assert compute_fingerprint({"a": 1, "b": 2}, None) == compute_fingerprint({"b": 2, "a": 1}, None)

    def test_matches_manual_sha256_of_sorted_json(self) -> None:
        doc = {"hostname": "sw01", "message": "link down"}
        expected = hashlib.sha256(json.dumps(doc, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        assert compute_fingerprint(doc, None) == expected

    def test_different_documents_produce_different_fingerprints(self) -> None:
        assert compute_fingerprint({"a": 1}, None) != compute_fingerprint({"a": 2}, None)

    def test_non_json_native_values_are_stringified(self) -> None:
        """`default=str` (ex. un objet non JSON-natif) ne doit jamais lever d'exception."""

        class _Weird:
            def __str__(self) -> str:
                return "weird"

        result = compute_fingerprint({"a": _Weird()}, None)
        assert result is not None


class TestSelectedFieldsFingerprint:
    """`fields=[...]` : hash d'une sélection ordonnée de champs, syntaxe %{...}."""

    def test_simple_field(self) -> None:
        result = compute_fingerprint({"hostname": "sw01"}, ["hostname"])
        assert result is not None
        assert len(result) == 64

    def test_nested_field_path(self) -> None:
        result = compute_fingerprint({"host": {"ip": "10.0.0.1"}}, ["[host][ip]"])
        assert result is not None

    def test_deterministic_for_same_input(self) -> None:
        doc = {"hostname": "sw01", "message": "link down"}
        assert compute_fingerprint(doc, ["hostname", "message"]) == compute_fingerprint(doc, ["hostname", "message"])

    def test_field_order_changes_fingerprint(self) -> None:
        doc = {"a": "x", "b": "y"}
        assert compute_fingerprint(doc, ["a", "b"]) != compute_fingerprint(doc, ["b", "a"])

    def test_different_field_split_does_not_collide(self) -> None:
        """Le séparateur de contrôle évite qu'"ab"/"c" se confonde avec "a"/"bc"."""
        result_1 = compute_fingerprint({"a": "ab", "b": "c"}, ["a", "b"])
        result_2 = compute_fingerprint({"a": "a", "b": "bc"}, ["a", "b"])
        assert result_1 != result_2

    def test_all_requested_fields_missing_returns_none(self) -> None:
        assert compute_fingerprint({"hostname": "sw01"}, ["nonexistent"]) is None

    def test_one_field_present_is_enough(self) -> None:
        result = compute_fingerprint({"hostname": "sw01"}, ["hostname", "nonexistent"])
        assert result is not None

    def test_null_field_counts_as_present(self) -> None:
        """Champ présent mais `null` : compte comme présent (décision #29).

        L'empreinte est celle du contenu vide (hash de ""), pas `None` —
        distinct d'un champ absent, qui seul exclut le champ.
        """
        result = compute_fingerprint({"hostname": None}, ["hostname"])
        assert result is not None
        assert result == compute_fingerprint({"hostname": ""}, ["hostname"])

    def test_null_and_absent_produce_different_outcomes(self) -> None:
        """Tout-null → empreinte ; tout-absent → `None` (distinction #29)."""
        all_null = compute_fingerprint({"a": None, "b": None}, ["a", "b"])
        all_absent = compute_fingerprint({"c": 1}, ["a", "b"])
        assert all_null is not None
        assert all_absent is None

    def test_null_field_joins_with_separator(self) -> None:
        """Null + valeur : le null contribue un segment vide au payload."""
        mixed = compute_fingerprint({"a": None, "b": "x"}, ["a", "b"])
        present = compute_fingerprint({"a": "", "b": "x"}, ["a", "b"])
        assert mixed == present


class TestHashMethod:
    """Sélection de l'algorithme de hachage."""

    def test_sha256_is_default(self) -> None:
        doc = {"hostname": "sw01"}
        assert compute_fingerprint(doc, ["hostname"]) == compute_fingerprint(doc, ["hostname"], "sha256")

    def test_sha1_produces_different_and_shorter_digest(self) -> None:
        doc = {"hostname": "sw01"}
        sha256_result = compute_fingerprint(doc, ["hostname"], "sha256")
        sha1_result = compute_fingerprint(doc, ["hostname"], "sha1")
        assert sha1_result != sha256_result
        assert len(sha1_result) == 40

    def test_md5_produces_32_char_digest(self) -> None:
        result = compute_fingerprint({"hostname": "sw01"}, ["hostname"], "md5")
        assert len(result) == 32

    def test_unknown_method_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="fingerprint inconnue"):
            compute_fingerprint({"hostname": "sw01"}, ["hostname"], "murmur3")
