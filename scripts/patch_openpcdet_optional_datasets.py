#!/usr/bin/env python3
"""Make OpenPCDet's optional Argo2 dataset registration lazy."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    args = parser.parse_args()

    target = args.source_dir / "pcdet" / "datasets" / "__init__.py"
    content = target.read_text(encoding="utf-8")
    if "try:\n    from .argo2.argo2_dataset import Argo2Dataset" in content:
        print("OpenPCDet optional dataset patch is already applied")
        return

    import_line = "from .argo2.argo2_dataset import Argo2Dataset\n"
    registry_line = "    'Argo2Dataset': Argo2Dataset\n"
    if import_line not in content or registry_line not in content:
        raise RuntimeError(f"Unsupported OpenPCDet dataset registry: {target}")

    content = content.replace(
        import_line,
        "try:\n    from .argo2.argo2_dataset import Argo2Dataset\nexcept ImportError:\n    Argo2Dataset = None\n",
    )
    content = content.replace(registry_line, "")
    marker = "}\n\n\nclass DistributedSampler"
    replacement = "}\n\nif Argo2Dataset is not None:\n    __all__['Argo2Dataset'] = Argo2Dataset\n\n\nclass DistributedSampler"
    if marker not in content:
        raise RuntimeError(f"Unsupported OpenPCDet dataset registry terminator: {target}")
    target.write_text(content.replace(marker, replacement), encoding="utf-8")
    print(f"Patched optional Argo2 dataset registration: {target}")


if __name__ == "__main__":
    main()
