#!/usr/bin/env bash
# Exit immediately if any command fails
set -o errexit

echo "--- 🚀 Starting Build Custom Audio Script ---"

# 1. Force Upgrade Pip
pip install --upgrade pip

# 2. Download a stable, pre-compiled static FFmpeg binary
echo "📥 Downloading FFmpeg audio dependencies..."
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

# 3. Extract the downloaded folder safely
echo "📦 Extracting files..."
tar -xf ffmpeg-release-amd64-static.tar.xz
rm ffmpeg-release-amd64-static.tar.xz

# 4. Relocate files into a clean project subdirectory
mkdir -p .ffmpeg
mv ffmpeg-*-amd64-static/ffmpeg .ffmpeg/
mv ffmpeg-*-amd64-static/ffprobe .ffmpeg/
rm -rf ffmpeg-*-amd64-static

# 5. Make sure the system permissions allow Python to execute them
chmod +x .ffmpeg/ffmpeg .ffmpeg/ffprobe

# 6. FORCE INSTALL THE REQUIREMENTS 
echo "🐍 Installing Python Pip packages..."
pip install -r requirements.txt

echo "--- 🎉 Build Script Finished Successfully! ---"
