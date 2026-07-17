FROM cv_ai_gpu:1.0

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

RUN ln -sf /usr/bin/python3 /usr/local/bin/python \
    && python -m pip install --upgrade pip setuptools wheel

RUN python -m pip install 'numpy<2'

# The existing image supplies CUDA 11.8, cuDNN, nvcc, and Python 3.10.
RUN python -m pip install torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cu118

RUN python -m pip install \
        av2==0.2.0 \
        easydict \
        numba \
        scikit-image \
        SharedArray \
        tensorboardX \
        tqdm \
        pyyaml \
        nuscenes-devkit==1.1.11 \
        spconv-cu118==2.3.6

# PyTorch 2.2 wheels are built against NumPy 1.x.
RUN python -m pip install --force-reinstall numpy==1.26.4

WORKDIR /workspace/OpenPCDet
