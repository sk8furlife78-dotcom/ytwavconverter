#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Download and extract a portable version of FFmpeg
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
rm ffmpeg-release-amd64-static.tar.xz

# 2. Move FFmpeg into a place where Python can see it
mkdir -p .ffmpeg
mv ffmpeg-*-amd64-static/ffmpeg .ffmpeg/
mv ffmpeg-*-amd64-static/ffprobe .ffmpeg/
rm -rf ffmpeg-*-amd64-static

# 3. Add FFmpeg to the temporary system path so Pydub finds it
export PATH=$PATH:$(pwd)/.ffmpeg

# 4. Install your Python packages standardly
pip install -r requirements.txt
