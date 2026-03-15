# VLFM Docker Environment - Updated with all fixes
# Original: Boston Dynamics AI Institute LLC, 2023
# Modified: Mar 2026 

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# ============================================================
# Step 1: System dependencies
#   - tmux: needed for VLM servers (launch_vlm_servers.sh)
#   - ffmpeg: needed for video generation (Habitat episode videos)
#   - unzip: needed for extracting dataset zips (ObjectNav, MP3D)
#   - wget: needed for downloading model weights and datasets
#   - openssh-client: needed for scp between lab machines
# ============================================================
RUN apt-get update \
      && apt-get install --no-install-recommends -qy curl apt-transport-https gnupg \
      sudo ca-certificates git software-properties-common \
      build-essential tmux ffmpeg unzip wget openssh-client \
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
#   - Do NOT include torch/torchvision here 
#   - opencv-python version left flexible 
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
#   - habitat-sim already installed via conda
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

# ============================================================
# Step 8: ffmpeg fix for video generation
#   - imageio-ffmpeg can't find system ffmpeg without this env var
#   - The parser in imageio-ffmpeg crashes when ffmpeg output lacks
#     "------" separator. Patch line 97 of _io.py to handle this.
#   - Without both fixes, Habitat episode video generation fails.
# ============================================================
ENV IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg

RUN python -c "\
path = '/opt/conda/envs/vlfm/lib/python3.9/site-packages/imageio_ffmpeg/_io.py'; \
f = open(path); code = f.read(); f.close(); \
old = '    footer = header_footer[1].strip(\"\\n\")'; \
new = '    footer = header_footer[1].strip(\"\\n\") if len(header_footer) > 1 else stdout.strip(\"\\n\")'; \
code = code.replace(old, new); \
f = open(path, 'w'); f.write(code); f.close(); \
print('imageio-ffmpeg parser patched successfully')"

# ============================================================
# Step 9: Make VLFM importable without pip install -e
#   - The VLFM source code is volume-mounted at /workspace/vlfm
#     at runtime -> can't pip install it at build time.
#   - PYTHONPATH tells Python to also look in /workspace/vlfm
#     when resolving imports like "from vlfm.policy import PointNavPolicy"
# ============================================================
ENV PYTHONPATH=/workspace/vlfm:$PYTHONPATH

# Set working directory
WORKDIR /workspace/vlfm

# ============================================================
# Step 10: Entrypoint script for runtime setup
#   - Runs automatically every time the container starts
#   - Copies GroundingDINO config to the path the launch script
#     expects. This can't be done at build time because the volume
#     mount at runtime overlays /workspace/vlfm/ and hides any
#     files created there during build
#   - Generates dummy PointNav policy weights if not present.
#   - Only runs these if the files don't already exist (first run)
# ============================================================
RUN printf '#!/bin/bash\n\
GDINO_DST=/workspace/vlfm/GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py\n\
GDINO_SRC=/opt/conda/envs/vlfm/lib/python3.9/site-packages/groundingdino/config/GroundingDINO_SwinT_OGC.py\n\
if [ ! -f "$GDINO_DST" ] && [ -f "$GDINO_SRC" ]; then\n\
    mkdir -p "$(dirname "$GDINO_DST")"\n\
    cp "$GDINO_SRC" "$GDINO_DST"\n\
    echo "GroundingDINO config copied to $GDINO_DST"\n\
fi\n\
if [ ! -f "/workspace/vlfm/data/dummy_policy.pth" ]; then\n\
    cd /workspace/vlfm && python -m vlfm.utils.generate_dummy_policy 2>/dev/null || true\n\
fi\n\
exec "$@"\n' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]