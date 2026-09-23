import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 교체 업로드 뒤 옛 영상 삭제. 되돌릴 수 없으므로
#  - 해냄이 채널 영상만 지운다(같은 계정의 다른 채널 보호)
#  - 영상 ID 를 --confirm 으로 한 번 더 받아 일치할 때만 지운다(교체본과 제목이 같아 눈으로는 구별이 안 된다)
EXPECTED_CHANNEL = "UCOJLKO6c_eSpp-PrITGcjBA"  # 해냄이

sys.stdout.reconfigure(encoding="utf-8")
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # 토큰은 늘 이 폴더 것만 쓴다
if len(sys.argv) not in (2, 4):
    sys.exit("사용법: python delete_video.py <video_id> [--confirm <video_id>]")
vid = sys.argv[1]
yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file("token_manage.json"))
r = yt.videos().list(part="snippet,status", id=vid).execute()
if not r.get("items"):
    sys.exit("영상 없음 또는 조회 권한 없음: " + vid)
sn = r["items"][0]["snippet"]
print("대상:", vid, "|", sn["channelTitle"], "|", sn["title"], "|", r["items"][0]["status"]["privacyStatus"])
if sn["channelId"] != EXPECTED_CHANNEL:
    sys.exit("해냄이 채널 영상이 아니다 — 중단")
if len(sys.argv) != 4 or sys.argv[2] != "--confirm" or sys.argv[3] != vid:
    sys.exit("미리보기만 했다 — 지우려면 --confirm " + vid)
yt.videos().delete(id=vid).execute()
print("삭제 완료:", vid)
