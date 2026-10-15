from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent / "src" / "mnemovela_client" / "_generated"
PROTO_DIR = HERE.parent.parent.parent / "contracts"  # clients/python -> repo root -> contracts
PROTO = PROTO_DIR / "mnemovela.v1.proto"

# protoc derives emitted module names from the proto FILENAME. The shared
# contract is named `mnemovela.v1.proto`, whose dots would yield awkward dotted /
# subpackage module names. We copy it (unmodified) to a temp dir under a flat,
# dot-free filename so protoc emits clean top-level modules we can ship as a
# self-contained package.
FLAT_STEM = "mnemovela_v1"
FLAT_NAME = f"{FLAT_STEM}.proto"


def main() -> int:
    PKG.mkdir(parents=True, exist_ok=True)
    (PKG / "__init__.py").write_text("", encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        flat_proto = tmp_dir / FLAT_NAME
        # copy verbatim; only the filename changes, `package mnemovela.v1;` stays put
        shutil.copyfile(PROTO, flat_proto)

        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"-I{tmp_dir}",
            f"--python_out={PKG}",
            f"--grpc_python_out={PKG}",
            str(flat_proto),
        ]
        subprocess.run(cmd, check=True)

    _fix_imports(PKG)
    print("generated stubs in", PKG)
    return 0


def _fix_imports(pkg: Path) -> None:
    # grpc_python_out emits `import mnemovela_v1_pb2 as ...` (a top-level import).
    # Rewrite it to a package-relative import so `_generated` is self-contained.
    pattern = re.compile(rf"^import {FLAT_STEM}_pb2 as", re.MULTILINE)
    replacement = f"from . import {FLAT_STEM}_pb2 as"
    for f in pkg.glob("*_pb2_grpc.py"):
        text = f.read_text(encoding="utf-8")
        new_text = pattern.sub(replacement, text)
        f.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
