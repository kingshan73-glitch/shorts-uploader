import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 교체 업로드 뒤 옛 영상 삭제. 되돌릴 수 없으므로 채널·제목을 먼저 출력하고 --yes 가 있을 때만 지운다
sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 2:
    sys.exit("사용법: python delete_video.py <video_id> [--yes]")
vid = sys.argv[1]
yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file("token_manage.json"))
r = yt.videos().list(part="snippet,status", id=vid).execute()
if not r.get("items"):
    sys.exit("영상 없음 또는 조회 권한 없음: " + vid)
sn = r["items"][0]["snippet"]
print("대상:", sn["channelTitle"], "|", sn["title"], "|", r["items"][0]["status"]["privacyStatus"])
if "--yes" not in sys.argv:
    sys.exit("미리보기만 했다 — 지우려면 --yes")
yt.videos().delete(id=vid).execute()
print("삭제 완료:", vid)
