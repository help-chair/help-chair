"""Jaro-Winkler y salvaguardas contra el over-merging."""

import pytest

from events.services.similarity import FuzzyConfig, compare_messages, jaro_winkler


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ("MARTHA", "MARHTA", 0.9611),  # valores de referencia de la literatura
        ("DIXON", "DICKSONX", 0.8133),
        ("DWAYNE", "DUANE", 0.84),
        ("abc", "abc", 1.0),
        ("abc", "xyz", 0.0),
        ("", "abc", 0.0),
    ],
)
def test_jaro_winkler_reference_values(a, b, expected):
    assert jaro_winkler(a, b) == pytest.approx(expected, abs=1e-3)


BASE = "no se puede conectar a la base de datos primary del cluster"


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (BASE, "no se puede conectar a la base de datos primary del cluster"),  # idénticos
        (BASE, "no se puede conectar a la base de datos primay del cluster"),  # errata
        (BASE, "no se puede conectar a la base de datos primaryy del cluster"),  # errata
    ],
)
def test_typos_are_duplicates(a, b):
    assert compare_messages(a, b).is_duplicate


@pytest.mark.parametrize(
    ("a", "b", "reason"),
    [
        (BASE, BASE.replace("primary", "replica"), "different_words"),  # otra palabra
        (
            "la solicitud falló con el código de estado 500 en el servidor",
            "la solicitud falló con el código de estado 404 en el servidor",
            "different_numbers",
        ),
        (BASE, BASE + " ahora mismo", "different_length"),  # palabras de más
        (
            BASE,
            BASE.replace("conectar", "iniciar").replace("primary", "replica"),
            "too_many_changes",
        ),
        ("error al leer", "error al leer!", "too_short"),
    ],
)
def test_over_merge_guards(a, b, reason):
    result = compare_messages(a, b)
    assert not result.is_duplicate
    assert result.reason == reason


def test_thresholds_are_configurable():
    strict = FuzzyConfig(threshold=0.999)
    typo = BASE.replace("primary", "primay")
    assert compare_messages(BASE, typo).is_duplicate
    assert not compare_messages(BASE, typo, strict).is_duplicate
