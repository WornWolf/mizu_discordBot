#!/bin/bash

# อัปเดตข้อมูลจาก package repository
apt-get update

# ติดตั้ง FFmpeg
apt-get install -y ffmpeg

# ติดตั้ง dependencies ที่ระบุใน requirements.txt
python -m pip install --upgrade yt-dlp
python -m pip install --upgrade pip  # อัปเกรด pip ให้เป็นเวอร์ชันล่าสุด
python -m pip install -r requirements.txt

# ตรวจสอบว่า cookies.txt มีอยู่ก่อนเริ่มการดาวน์โหลด
if [[ ! -f cookies.txt ]]; then
  echo "Error: ไม่พบ cookies.txt โปรดสร้างไฟล์นี้ก่อนที่จะรันสคริปต์"
  exit 1
fi

# ดาวน์โหลดเสียงหรือวิดีโอจาก YouTube โดยใช้ yt-dlp พร้อม cookies.txt
yt-dlp --cookies cookies.txt -f bestaudio/best "URL ของ YouTube"
