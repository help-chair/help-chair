"""Compara el esquema que genera el código con el contrato escrito a mano.

El contrato de `contracts/access/openapi.yaml` es la fuente de verdad: declara
endpoints que el código todavía no sirve y que Plataforma y Frontend ya leen.
Por eso este script nunca escribe sobre el contrato; solo compara y reporta.

Falla (salida 1) cuando el código sirve algo que el contrato no declara, porque
eso es la API corriendo por delante del contrato. Lo contrario (el contrato
declara algo que el código no sirve todavía) es lo normal durante el desarrollo
y solo se informa.

Uso:
    python tools/reconcilia_contrato.py GENERADO.yaml CONTRATO.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

METODOS = ("get", "post", "put", "patch", "delete", "head", "options")


def cargar(ruta: Path) -> dict[str, Any]:
    if not ruta.exists():
        print(f"ERROR: no existe {ruta}")
        raise SystemExit(2)
    with ruta.open(encoding="utf-8") as f:
        datos = yaml.safe_load(f)
    if not isinstance(datos, dict) or "paths" not in datos:
        print(f"ERROR: {ruta} no parece un OpenAPI con 'paths'")
        raise SystemExit(2)
    return datos


def operaciones(doc: dict[str, Any]) -> set[tuple[str, str]]:
    halladas = set()
    for ruta, cuerpo in (doc.get("paths") or {}).items():
        if not isinstance(cuerpo, dict):
            continue
        for metodo in cuerpo:
            if metodo.lower() in METODOS:
                halladas.add((ruta, metodo.lower()))
    return halladas


def resolver(doc: dict[str, Any], nodo: Any, visitados: frozenset[str] = frozenset()) -> Any:
    """Sigue un $ref dentro del mismo documento, sin entrar en ciclos."""
    while isinstance(nodo, dict) and "$ref" in nodo:
        ref = nodo["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/") or ref in visitados:
            return nodo
        visitados = visitados | {ref}
        actual: Any = doc
        for parte in ref[2:].split("/"):
            if not isinstance(actual, dict) or parte not in actual:
                return nodo
            actual = actual[parte]
        nodo = actual
    return nodo


def campos_de_respuesta(doc: dict[str, Any], ruta: str, metodo: str) -> set[str]:
    """Nombres de campo de la respuesta 200/201 en application/json."""
    operacion = resolver(doc, (doc.get("paths") or {}).get(ruta, {}).get(metodo, {}))
    if not isinstance(operacion, dict):
        return set()
    respuestas = resolver(doc, operacion.get("responses") or {})
    if not isinstance(respuestas, dict):
        return set()
    for codigo in ("200", "201", 200, 201):
        respuesta = resolver(doc, respuestas.get(codigo))
        if not isinstance(respuesta, dict):
            continue
        contenido = resolver(doc, respuesta.get("content") or {})
        if not isinstance(contenido, dict):
            continue
        json = resolver(doc, contenido.get("application/json") or {})
        if not isinstance(json, dict):
            continue
        esquema = resolver(doc, json.get("schema") or {})
        if isinstance(esquema, dict) and isinstance(esquema.get("properties"), dict):
            return set(esquema["properties"].keys())
    return set()


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2

    ruta_generado, ruta_contrato = Path(argv[1]), Path(argv[2])
    generado, contrato = cargar(ruta_generado), cargar(ruta_contrato)

    ops_generado, ops_contrato = operaciones(generado), operaciones(contrato)
    sin_declarar = sorted(ops_generado - ops_contrato)
    sin_servir = sorted(ops_contrato - ops_generado)
    compartidas = sorted(ops_generado & ops_contrato)

    print(f"contrato : {len(ops_contrato)} operaciones en {ruta_contrato}")
    print(f"generado : {len(ops_generado)} operaciones desde el código")
    print(f"en ambos : {len(compartidas)}")

    if sin_servir:
        print(f"\nDeclaradas en el contrato y aún no servidas ({len(sin_servir)}), normal:")
        for ruta, metodo in sin_servir:
            print(f"  · {metodo.upper():6} {ruta}")

    desajustes = []
    for ruta, metodo in compartidas:
        del_codigo = campos_de_respuesta(generado, ruta, metodo)
        del_contrato = campos_de_respuesta(contrato, ruta, metodo)
        if not del_codigo or not del_contrato:
            continue
        if del_codigo != del_contrato:
            desajustes.append((ruta, metodo, del_codigo, del_contrato))

    if desajustes:
        print(f"\nCampos de respuesta que no concuerdan ({len(desajustes)}):")
        for ruta, metodo, del_codigo, del_contrato in desajustes:
            print(f"  · {metodo.upper()} {ruta}")
            if sobran := sorted(del_codigo - del_contrato):
                print(f"      el código entrega y el contrato no declara: {', '.join(sobran)}")
            if faltan := sorted(del_contrato - del_codigo):
                print(f"      el contrato declara y el código no entrega: {', '.join(faltan)}")

    if sin_declarar:
        print(f"\nFALLA: el código sirve {len(sin_declarar)} operación(es) sin declarar:")
        for ruta, metodo in sin_declarar:
            print(f"  · {metodo.upper():6} {ruta}")
        print("\nDeclara esas operaciones en el contrato antes de seguir.")
        return 1

    if desajustes:
        print("\nFALLA: hay campos de respuesta que no concuerdan (ver arriba).")
        return 1

    print("\nOK: el contrato declara todo lo que el código sirve, y los campos concuerdan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
