"""Similitud entre mensajes (Jaro-Winkler) con salvaguardas contra el *over-merging*.

Jaro-Winkler por sí solo fusiona de más: dos mensajes largos que difieren en una sola palabra
("... base de datos primary ..." vs "... base de datos replica ...") puntúan casi 1.0. Por eso
`compare_messages` exige además que las diferencias sean erratas y no palabras o números distintos.
"""

from dataclasses import dataclass


def jaro(a: str, b: str) -> float:
    """Similitud de Jaro entre dos cadenas (0.0 a 1.0)."""
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    window = max(max(la, lb) // 2 - 1, 0)
    a_matched = [False] * la
    b_matched = [False] * lb
    matches = 0
    for i, ch in enumerate(a):
        for j in range(max(0, i - window), min(lb, i + window + 1)):
            if not b_matched[j] and b[j] == ch:
                a_matched[i] = b_matched[j] = True
                matches += 1
                break
    if matches == 0:
        return 0.0
    transpositions = 0
    j = 0
    for i in range(la):
        if a_matched[i]:
            while not b_matched[j]:
                j += 1
            if a[i] != b[j]:
                transpositions += 1
            j += 1
    transpositions //= 2
    return (matches / la + matches / lb + (matches - transpositions) / matches) / 3


def jaro_winkler(a: str, b: str, *, prefix_scale: float = 0.1, max_prefix: int = 4) -> float:
    """Jaro-Winkler: Jaro con un bono por prefijo común (hasta `max_prefix` caracteres)."""
    base = jaro(a, b)
    prefix = 0
    for ca, cb in zip(a, b, strict=False):
        if ca != cb or prefix == max_prefix:
            break
        prefix += 1
    return base + prefix * prefix_scale * (1 - base)


@dataclass(frozen=True)
class FuzzyConfig:
    threshold: float = 0.95  # Jaro-Winkler mínimo del mensaje completo
    token_threshold: float = 0.88  # Jaro-Winkler mínimo de la palabra que cambia
    max_diff_tokens: int = 1  # cuántas palabras pueden diferir
    min_length: int = 20  # mensajes más cortos no se comparan por similitud


@dataclass(frozen=True)
class Similarity:
    is_duplicate: bool
    score: float
    reason: str  # identical | typo | too_short | different_length | too_many_changes | ...


def compare_messages(a: str, b: str, config: FuzzyConfig | None = None) -> Similarity:
    """¿Son `a` y `b` (ya normalizados) el mismo mensaje con una errata o variación mínima?"""
    config = config or FuzzyConfig()
    if a == b:
        return Similarity(True, 1.0, "identical")
    score = jaro_winkler(a, b)
    if min(len(a), len(b)) < config.min_length:
        return Similarity(False, score, "too_short")

    tokens_a, tokens_b = a.split(), b.split()
    if len(tokens_a) != len(tokens_b):  # agregar o quitar palabras cambia el significado
        return Similarity(False, score, "different_length")
    changed = [(x, y) for x, y in zip(tokens_a, tokens_b, strict=True) if x != y]
    if len(changed) > config.max_diff_tokens:
        return Similarity(False, score, "too_many_changes")
    for x, y in changed:
        if any(ch.isdigit() for ch in x + y):  # 500 vs 404, v1.2 vs v1.3: no son erratas
            return Similarity(False, score, "different_numbers")
        if jaro_winkler(x, y) < config.token_threshold:  # primary vs replica
            return Similarity(False, score, "different_words")
    if score < config.threshold:
        return Similarity(False, score, "low_score")
    return Similarity(True, score, "typo")
