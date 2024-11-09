#!/bin/bash
apt-get update && apt-get install -y ffmpeg
# ต่อจากนั้นรันคำสั่ง build ของคุณ
python -m pip install -r requirements.txt
