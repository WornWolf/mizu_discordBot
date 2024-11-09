#!/bin/bash

# อัปเดตข้อมูลจาก package repository
apt-get update

# ติดตั้ง FFmpeg
apt-get install -y ffmpeg

# ติดตั้ง dependencies ที่ระบุใน requirements.txt
python -m pip install --upgrade pip  # อัปเกรด pip ให้เป็นเวอร์ชันล่าสุด
python -m pip install -r requirements.txt
