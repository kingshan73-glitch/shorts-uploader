# -*- coding: utf-8 -*-
"""예약 공개 시각 조회·일괄 변경 (본인 채널 전용).

`upload_shorts.py` 는 업로드만 하므로 스코프가 `youtube.upload` 하나다.
예약 시각을 **읽거나 고치려면** `youtube` 스코프가 필요해 토큰을 따로 둔다
(`token_manage.json`). 업로더 토큰(`token.json`)은 건드리지 않는다.

  python manage_schedule.py --list                     # 예약 목록만 본다
  python manage_schedule.py --set-time 18:00           # 미리보기(기본 dry-run)
  python manage_schedule.py --set-time 18:00 --apply   # 실제 변경

--set-time 은 **시:분만** 바꾼다. 각 영상의 예약 날짜는 그대로 둔다.
이미 그 시각인 영상, 공개된 영상, 예약이 없는 영상은 건너뛴다.
"""
import argparse
import datetime
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube"]
KST = datetime.timezone(datetime.timedelta(hours=9))


def get_service(client_secret, token_path):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 브라우저를 자동으로 열지 않고 URL 을 출력한다.
            # 자동으로 열면 이 세션이 제어할 수 없는 창이 떠 인증이 멈춘 채로 대기한다.
            flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
            print("[인증] 아래 URL 을 열어 권한을 허용하세요.", flush=True)
            creds = flow.run_local_server(port=8765, open_browser=False)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def my_uploads_playlist(yt):
    r = yt.channels().list(part="contentDetails", mine=True).execute()
    return r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def all_video_ids(yt, playlist_id):
    ids, token = [], None
    while True:
        r = yt.playlistItems().list(
            part="contentDetails", playlistId=playlist_id, maxResults=50, pageToken=token
        ).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        token = r.get("nextPageToken")
        if not token:
            return ids


def fetch(yt, ids):
    out = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,status", id=",".join(ids[i:i + 50])).execute()
        out += r["items"]
    return out


def scheduled(items):
    rows = []
    for v in items:
        st = v["status"]
        if st.get("privacyStatus") != "private" or not st.get("publishAt"):
            continue
        at = datetime.datetime.fromisoformat(st["publishAt"].replace("Z", "+00:00")).astimezone(KST)
        rows.append({"id": v["id"], "title": v["snippet"]["title"], "at": at})
    rows.sort(key=lambda r: r["at"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-secret", default="client_secret.json")
    ap.add_argument("--token", default="token_manage.json")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--set-time", help="HH:MM (KST). 날짜는 그대로 두고 시각만 바꾼다")
    ap.add_argument("--apply", action="store_true", help="실제로 변경한다(없으면 미리보기)")
    a = ap.parse_args()

    yt = get_service(a.client_secret, a.token)
    rows = scheduled(fetch(yt, all_video_ids(yt, my_uploads_playlist(yt))))

    print("\n예약된 영상 %d편\n" % len(rows))
    for r in rows:
        wd = "월화수목금토일"[r["at"].weekday()]
        print("  %s(%s) %s  %s  %s" % (
            r["at"].strftime("%Y-%m-%d"), wd, r["at"].strftime("%H:%M"), r["id"], r["title"][:44]))

    times = sorted({r["at"].strftime("%H:%M") for r in rows})
    print("\n현재 쓰이는 시각: %s" % ", ".join(times))

    if a.list or not a.set_time:
        return

    hh, mm = [int(x) for x in a.set_time.split(":")]
    targets = [r for r in rows if r["at"].strftime("%H:%M") != a.set_time]
    print("\n%s 로 바꿀 대상 %d편 (이미 맞는 %d편은 건너뜀)" % (a.set_time, len(targets), len(rows) - len(targets)))
    for r in targets:
        print("  %s  %s → %s  %s" % (r["id"], r["at"].strftime("%H:%M"), a.set_time, r["title"][:40]))

    if not a.apply:
        print("\n미리보기입니다. 실제로 바꾸려면 --apply 를 붙이세요.")
        return

    ok = 0
    for r in targets:
        new_at = r["at"].replace(hour=hh, minute=mm, second=0, microsecond=0)
        v = yt.videos().list(part="status", id=r["id"]).execute()["items"][0]
        st = v["status"]
        body = {
            "id": r["id"],
            "status": {
                "privacyStatus": "private",
                "publishAt": new_at.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                "selfDeclaredMadeForKids": st.get("selfDeclaredMadeForKids", False),
                "license": st.get("license", "youtube"),
                "embeddable": st.get("embeddable", True),
                "publicStatsViewable": st.get("publicStatsViewable", True),
            },
        }
        yt.videos().update(part="status", body=body).execute()
        ok += 1
        print("  변경 %s → %s %s" % (r["id"], new_at.strftime("%Y-%m-%d %H:%M"), r["title"][:36]))
    print("\n%d편 변경 완료" % ok)


if __name__ == "__main__":
    main()
