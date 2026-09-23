import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 2:
    sys.exit("사용법: python check_video.py <video_id>")
creds = Credentials.from_authorized_user_file("token_manage.json")
yt = build("youtube", "v3", credentials=creds)
r = yt.videos().list(part="snippet,status,contentDetails", id=sys.argv[1]).execute()
if not r.get("items"):
    sys.exit("영상 없음 또는 조회 권한 없음: " + sys.argv[1])
for v in r["items"]:
    print(v["snippet"]["channelTitle"], v["snippet"]["channelId"])
    print(v["snippet"]["title"])
    print(v["status"]["privacyStatus"], v["status"]["uploadStatus"], v["contentDetails"]["duration"])
