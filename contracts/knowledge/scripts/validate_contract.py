"""Validate the KB draft without Django, databases, environment files or credentials."""

import argparse
import copy
import json
import subprocess
from pathlib import Path

import yaml
from jsonschema import FormatChecker
from openapi_schema_validator import OAS30ReadValidator, OAS30WriteValidator
from openapi_spec_validator import validate_spec

MODEL_COMMIT = "4f8573d442de3c01a4f866d5468f3f4ac6e2d4ec"
METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


class ContractError(Exception):
    """A validation failure whose message contains no instance values."""


class UniqueLoader(yaml.SafeLoader):
    """Fail on duplicate mapping keys instead of silently replacing an operation."""


def unique_mapping(loader, node):
    pairs = loader.construct_pairs(node)
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("Duplicate YAML key")
        result[key] = value
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def resolve(document, value, seen=()):
    if isinstance(value, list):
        return [resolve(document, item, seen) for item in value]
    if not isinstance(value, dict):
        return value
    if "$ref" in value:
        ref = value["$ref"]
        if not ref.startswith("#/") or ref in seen:
            raise ContractError("Only non-circular local references are allowed")
        target = document
        for part in ref[2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        return resolve(document, target, (*seen, ref))
    return {key: resolve(document, item, seen) for key, item in value.items()}


def valid(schema, value, *, write=False):
    validator = OAS30WriteValidator if write else OAS30ReadValidator
    return not any(validator(schema, format_checker=FormatChecker()).iter_errors(value))


def require(condition, label):
    if not condition:
        raise ContractError(label)


def check_media(media, *, write=False):
    count = 0
    for body in media.values():
        schema = body.get("schema")
        if schema is None:
            continue
        values = [item["value"] for item in body.get("examples", {}).values()]
        if "example" in body:
            values.append(body["example"])
        require(bool(values), "A request/response media type has no reviewable example")
        for value in values:
            require(
                valid(schema, value, write=write), "Request/response example is invalid"
            )
            count += 1
    return count


def validate(document):
    # Resolve before the spec validator so it cannot retrieve external resources.
    expanded = resolve(document, document)
    validate_spec(document)
    require(document["openapi"] == "3.0.3", "Unexpected OpenAPI dialect")
    require(document["x-model-commit"] == MODEL_COMMIT, "Model reference changed")
    require(document["security"] == [{"bearerAuth": []}], "Business security missing")
    count = 0
    operations = 0
    for path, path_item in expanded["paths"].items():
        for method, operation in path_item.items():
            if method not in METHODS:
                continue
            operations += 1
            health = path.startswith("/health/")
            expected = "existente-en-codigo" if health else "prevista"
            require(
                operation["x-implementation-status"] == expected,
                "Implementation status",
            )
            if health:
                require(operation.get("security") == [], "Health must be public")
            else:
                require("security" not in operation, "Business security was overridden")
            if "requestBody" in operation:
                count += check_media(operation["requestBody"]["content"], write=True)
            for response in operation["responses"].values():
                count += check_media(response.get("content", {}))
            parameters = path_item.get("parameters", []) + operation.get(
                "parameters", []
            )
            for parameter in parameters:
                schema = parameter["schema"]
                if "default" in schema:
                    require(
                        valid(schema, schema["default"]), "Invalid parameter default"
                    )
    require(
        operations == 7, "Expected five business operations and two health operations"
    )
    return expanded, count, operations


def negative_cases(document):
    schemas = document["components"]["schemas"]
    examples = document["components"]["examples"]
    article = examples["PublicadoEmpresa"]["value"]
    cases = []
    for key, value in (
        ("id", "KB-028"),
        ("titulo", "x" * 201),
        ("titulo", " \n\t"),
        ("contenido", " \n\t"),
        ("categoria", None),
        ("categoria", "red\n"),
        ("autor_id", None),
        ("publicado_en", None),
        ("creado_en", "not-a-date"),
        ("archivado_en", "2026-11-21T14:00:00Z"),
        ("estado", "revisado"),
        ("visibilidad", "publico"),
        ("resumen", "Not part of the initial model"),
    ):
        value_copy = copy.deepcopy(article)
        value_copy[key] = value
        cases.append(("Articulo", value_copy, False))
    archived = copy.deepcopy(examples["Archivado"]["value"])
    archived["archivado_en"] = None
    cases.append(("Articulo", archived, False))
    missing_id = copy.deepcopy(article)
    del missing_id["id"]
    cases.append(("Articulo", missing_id, False))
    for field in ("id", "autor_id", "empresa", "estado", "creado_en", "actualizado_en"):
        cases.append(("ArticuloCrear", {field: "not-client-controlled"}, True))
        cases.append(("ArticuloActualizar", {field: "not-client-controlled"}, True))
    cases.extend(
        [
            ("ArticuloActualizar", {}, True),
            ("ArticuloActualizar", {"titulo": None}, True),
            ("ArticuloCrear", {"contenido": None}, True),
            ("ArticuloCrear", {"categoria": "red\n"}, True),
            ("TextoConsulta", "   \t", True),
            ("TextoConsulta", "x" * 201, True),
        ]
    )
    for name in ("Borrador", "Archivado"):
        page = {"count": 1, "next": None, "previous": None}
        page["results"] = [examples[name]["value"]]
        cases.append(("PaginaSoluciones", page, False))
    for schema_name, value, write in cases:
        require(
            not valid(schemas[schema_name], value, write=write),
            "Negative case accepted",
        )
    parameters = document["components"]["parameters"]
    for value, schema in (
        (0, parameters["Pagina"]["schema"]),
        (101, parameters["TamanoPagina"]["schema"]),
    ):
        require(not valid(schema, value), "Pagination bound accepted")
    return len(cases) + 2


def compare_fixture(document, repo):
    # git show is read-only and pins the source independently of the active checkout.
    result = subprocess.run(
        [
            "git",
            "--no-optional-locks",
            "-C",
            str(repo),
            "show",
            f"{MODEL_COMMIT}:services/knowledge/articles/fixtures/kb_demo.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = json.loads(result.stdout)
    names = {"borrador": "Borrador", "archivado": "Archivado"}
    checked = 0
    for row in rows:
        if row["model"] != "articles.articulo":
            continue
        fields = row["fields"]
        name = names.get(
            fields["estado"], "Publicado" + fields["visibilidad"].capitalize()
        )
        expected = {"id": row["pk"], **fields}
        actual = document["components"]["examples"][name]["value"]
        require(actual == expected, "Canonical fixture example drifted")
        require(len(actual["id"]) <= 64, "Problems external reference too short")
        checked += 1
    require(checked == 4, "Canonical article examples are missing")
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "openapi.yaml",
    )
    parser.add_argument(
        "--repo", type=Path, help="Optional checkout for read-only pinned fixture check"
    )
    args = parser.parse_args()
    document = yaml.load(args.spec.read_text(encoding="utf-8"), Loader=UniqueLoader)
    expanded, count, operations = validate(document)
    negatives = negative_cases(expanded)
    fixtures = compare_fixture(document, args.repo) if args.repo else 0
    print(
        f"PASS OpenAPI 3.0.3; operations={operations}; examples={count}; "
        f"negative_cases={negatives}; pinned_fixture_articles={fixtures}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Do not echo schema instances, subprocess output, tokens or process environment.
        print(
            f"FAIL contract validation ({type(error).__name__}); inspect locally without secrets"
        )
        if isinstance(error, ContractError):
            print(
                str(error)
            )  # Only fixed labels authored above, never instance values.
        elif hasattr(error, "path"):
            print("Schema location:", "/".join(map(str, error.path)))
            for context in getattr(error, "context", []):
                print("Schema context:", "/".join(map(str, context.schema_path)))
        raise SystemExit(1) from None
