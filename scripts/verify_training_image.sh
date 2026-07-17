#!/usr/bin/env bash
set -euo pipefail

image_name="${IMAGE_NAME:-robot-3d-detection:cuda12.1}"

docker run --rm --gpus all -i "$image_name" python - <<'PY'
import torch
import spconv
import spconv.pytorch as spconv_pytorch

assert torch.cuda.is_available(), "CUDA is not visible in the container"
print(f"torch={torch.__version__}")
print(f"cuda={torch.version.cuda}")
print(f"gpu={torch.cuda.get_device_name(0)}")
print(f"spconv={spconv.__version__}")
PY
