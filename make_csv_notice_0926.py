import csv
import os
import shutil
import sys

SRC = r"D:\Claude_code_project\digital_content\outputs\홈페이지점검_쇼츠_20260923\홈페이지점검안내_0926_16s_1080x1920-02_첫프레임보강.mp4"
FILE = "홈페이지점검안내_0926.mp4"
# 업로드 기록(status·video_id)을 덮어써 중복 업로드되는 것을 막는다
if os.path.exists("videos_notice_0926.csv"):
    sys.exit("videos_notice_0926.csv 가 이미 있다 — 업로드 기록 보호를 위해 중단")
shutil.copyfile(SRC, "videos/" + FILE)

title = "9월 26일(토) 해냄에듀 홈페이지 시스템 점검 안내 | 09:00~18:00 #Shorts"
desc = "\n".join([
    "해냄에듀 홈페이지가 9월 26일(토) 하루, 시스템 점검으로 잠시 쉬어 갑니다.",
    "더욱 안전하고 편리한 서비스 이용을 위해 보안 강화 및 서비스 안정성 향상을 위한 시스템 개선 작업을 진행합니다.",
    "",
    "■ 점검일시: 9월 26일(토) 09:00~18:00",
    "■ 점검 시간 동안 홈페이지 접속 및 서비스 이용이 잠시 중단됩니다.",
    "",
    "수업에 필요한 자료는 점검 전에 미리 받아 두세요.",
    "더 나은 서비스로 찾아뵙겠습니다. 감사합니다.",
    "",
    "▶ 해냄에듀 홈페이지: https://www.hnedu.co.kr/?utm_source=youtube&utm_medium=shorts&utm_campaign=maintenance_20260926",
    "",
    "#해냄에듀 #시스템점검 #공지사항",
])
tags = "해냄에듀;시스템점검;홈페이지점검;공지사항;shorts"

with open("videos_notice_0926.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["file", "title", "description", "tags", "publish_at", "status", "video_id", "url"])
    w.writeheader()
    w.writerow({"file": FILE, "title": title, "description": desc, "tags": tags})
print("ok", len(title))
