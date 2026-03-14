# VLFM Docker Environment - Updated with all fixes
# Original: Boston Dynamics AI Institute LLC, 2023
# Modified: Feb 2026 - CMU CERLAB

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# ============================================================
# Step 1: System dependencies + tmux (needed for VLM servers)
# ============================================================
RUN apt-get update \
      && apt-get install --no-install-recommends -qy curl apt-transport-https gnupg \
      sudo ca-certificates git software-properties-common \
      build-essential tmux \
      libgl1-mesa-dev libjpeg-dev libglm-dev libgl1-mesa-glx \
      libegl1-mesa-dev mesa-utils xorg-dev freeglut3-dev \
      && rm -rf /var/lib/apt/lists/* \
      && apt-get clean all

# ============================================================
# Step 2: Install Miniconda (needed for habitat-sim)
# ============================================================
RUN curl -sL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
      && bash /tmp/miniconda.sh -b -p /opt/conda \
      && rm /tmp/miniconda.sh

ENV PATH=/opt/conda/bin:$PATH

# ============================================================
# Step 3: Create conda env + install habitat-sim via conda
#   - Must accept conda TOS first (non-interactive mode)
#   - habitat-sim cannot be built from source (CMake/corrade bug)
#   - "headless" = no display needed 
# ============================================================
RUN conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main \
      && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r \
      && conda create -n vlfm python=3.9 -y \
      && conda install -n vlfm habitat-sim=0.2.4 headless -c conda-forge -c aihabitat -y

# Activate conda env for all subsequent RUN commands
ENV PATH=/opt/conda/envs/vlfm/bin:$PATH
ENV CONDA_DEFAULT_ENV=vlfm

# ============================================================
# Step 4: Install PyTorch 2.0.1 with CUDA 11.8
#   - MUST use 2.0+ for Ada Lovelace GPUs (RTX 4070/4090)
#   - The original pinned torch==1.12.1 does NOT support these GPUs
#   - Pin numpy==1.26.4 to avoid cv2 incompatibility
# ============================================================
RUN pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 \
      --index-url https://download.pytorch.org/whl/cu118

RUN pip install numpy==1.26.4

# ============================================================
# Step 5: Install remaining Python packages
#   - Do NOT include torch/torchvision here (already installed above)
#   - opencv-python version left flexible (4.5.5.64 is fine too)
# ============================================================
RUN pip install \
    flask>=2.3.2 \
    seaborn>=0.12.2 \
    open3d>=0.17.0 \
    transformers==4.26.0 \
    salesforce-lavis>=1.0.2 \
    pre-commit>=3.1.1 \
    pytest>=7.2.1 \
    pytest-cov>=4.0.0 \
    habitat-baselines==0.2.420230405 \
    habitat-lab==0.2.420230405 \
    bosdyn-client>=3.3.2 \
    bosdyn-api>=3.3.2 \
    six>=1.16.0 \
    opencv-python

# ============================================================
# Step 6: Install git dependencies
#   - habitat-sim already installed via conda, do NOT include it
#   - GroundingDINO must use --no-build-isolation (setup.py imports torch)
# ============================================================
RUN pip install git+https://github.com/naokiyokoyama/frontier_exploration.git \
                git+https://github.com/ChaoningZhang/MobileSAM.git \
                git+https://github.com/naokiyokoyama/depth_camera_filtering \
                git+https://github.com/naokiyokoyama/bd_spot_wrapper.git

RUN pip install --no-build-isolation git+https://github.com/IDEA-Research/GroundingDINO.git

# ============================================================
# Step 7: Fix numpy/torch versions that may have been overridden
#   - salesforce-lavis or other packages may downgrade torch
#   - Reinstall correct versions as final step to guarantee them
# ============================================================
RUN pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 \
      --index-url https://download.pytorch.org/whl/cu118 \
    && pip install numpy==1.26.4

RUN apt-get update && apt-get install -y wget

# Set working directory
WORKDIR /workspace/vlfm
