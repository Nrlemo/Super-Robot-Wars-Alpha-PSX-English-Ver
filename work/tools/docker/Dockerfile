# Contenedor de emulación para máquinas sin monitor (server1): Xvfb + Mesa (OpenGL por software).
# El proyecto se monta en la misma ruta que en el host; los emuladores son los de work/tools/bin.
# Build:  docker build -t srw-emu "work/tools/docker"
FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive LIBGL_ALWAYS_SOFTWARE=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      xvfb xauth mesa-utils libgl1 libgl1-mesa-dri libglx-mesa0 libegl1 libegl-mesa0 libgles2 \
      libglib2.0-0t64 libx11-6 libx11-xcb1 libxext6 libxrandr2 libxi6 libxcursor1 libxinerama1 \
      libxkbcommon0 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 \
      libxcb-xinerama0 libxcb-randr0 libxcb-render-util0 libxcb-image0 libasound2t64 libpulse0 \
      libfontconfig1 libfreetype6 libfribidi0 libharfbuzz0b libdbus-1-3 ca-certificates coreutils procps \
    && rm -rf /var/lib/apt/lists/*
