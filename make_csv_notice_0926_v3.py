import csv
import os
import shutil
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 깜빡임 수정본(-03)으로 교체 업로드. 메타데이터는 1차 업로드 CSV 를 그대로 쓴다
SRC = r"D:\Claude_code_project\digital_content\outputs\홈페이지점검_쇼츠_20260923\홈페이지점검안내_0926_16s_1080x1920-03_깜빡임수정.mp4"
FILE = "홈페이지점검안내_0926_v3.mp4"
OUT = "videos_notice_0926_v3.csv"
if os.path.exists(OUT):
    sys.exit(OUT + " 가 이미 있다 — 업로드 기록 보호를 위해 중단")

with open("videos_notice_0926.csv", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
if len(rows) != 1:
    sys.exit(f"원본 CSV 행이 {len(rows)}개 — 1행이어야 한다")
row = dict(rows[0])
row.update({"file": FILE, "status": "", "video_id": "", "url": ""})

shutil.copyfile(SRC, "videos/" + FILE)
with open(OUT, "x", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerow(row)
print("ok", row["title"])
