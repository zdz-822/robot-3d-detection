#!/usr/bin/env python3
"""Apply the NumPy 1.24+ compatibility fix required by OpenPCDet 0.6."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    args = parser.parse_args()

    target = args.source_dir / "pcdet" / "models" / "backbones_2d" / "base_bev_backbone.py"
    content = target.read_text(encoding="utf-8")
    deprecated = "np.round(1 / stride).astype(np.int)"
    compatible = "np.round(1 / stride).astype(int)"
    if compatible in content:
        print("OpenPCDet NumPy compatibility patch is already applied")
        return
    if deprecated not in content:
        raise RuntimeError(f"Unsupported OpenPCDet backbone implementation: {target}")
    target.write_text(content.replace(deprecated, compatible), encoding="utf-8")
    print(f"Patched NumPy compatibility: {target}")


if __name__ == "__main__":
    main()
