"""Exportación explícita del runtime que no puede sustituir contratos revisados."""

import os
import subprocess
import sys
from pathlib import Path

service = Path(__file__).resolve().parents[1]
output = os.environ.get("OPENAPI_OUTPUT", "")
if not output.strip():
    raise SystemExit("OPENAPI_OUTPUT: requiere un destino explícito fuera de contracts/")
target = Path(output).expanduser().resolve()
contracts = service.parents[1] / "contracts"
if target.is_relative_to(contracts.resolve()):
    raise SystemExit("OPENAPI_OUTPUT: no se permite sobrescribir contracts/")
target.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(
    [sys.executable, "manage.py", "spectacular", "--file", str(target), "--validate"],
    cwd=service,
    check=True,
)
