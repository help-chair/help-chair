"""Optional redacted artifact scan; never emits detected values or a baseline."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def main():
    root = Path(__file__).resolve().parents[1]
    executable = shutil.which("detect-secrets")
    if executable is None:
        sibling = Path(sys.executable).parent / "detect-secrets"
        executable = str(sibling) if sibling.is_file() else None
    if executable is None:
        print("FAIL scanner unavailable; prepare detect-secrets separately")
        return 2
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".yaml", ".md", ".py", ".mjs"}
    )
    with TemporaryDirectory(prefix="helpchair-contract-scan-") as temporary:
        result = subprocess.run(
            [executable, "scan", "--all-files", "--no-verify", *map(str, files)],
            cwd=temporary,
            capture_output=True,
            text=True,
            check=True,
        )
    findings = json.loads(result.stdout)["results"]
    count = sum(map(len, findings.values()))
    print(
        f"{'FAIL' if count else 'PASS'} artifact scan: files={len(files)}; findings={count}"
    )
    for filename, items in findings.items():
        # Only locations/types; never values, hashes, output/stderr or line content.
        for item in items:
            relative = Path(filename).relative_to(root)
            print(f"Review locally: {relative}:{item['line_number']} ({item['type']})")
    return int(bool(count))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"FAIL scanner ({type(error).__name__}); details suppressed")
        raise SystemExit(2) from None
