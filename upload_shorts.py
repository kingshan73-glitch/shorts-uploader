#!/usr/bin/env python3
"""Shorts Batch Uploader - 로컬 폴더의 mp4 를 CSV 메타데이터로 본인 채널에 일괄 업로드."""
import argparse
import csv
import os
import sys
import time

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CSV_FIELDS = ["file", "title", "description", "tags", "publish_at", "status", "video_id", "url"]
CHUNK_SIZE = 8 * 1024 * 1024
MAX_RETRIES = 3


def parse_args():
    p = argparse.ArgumentParser(description="Shorts Batch Uploader")
    p.add_argument("--csv", default="videos.csv", help="메타데이터 CSV (기본 videos.csv)")
    p.add_argument("--dir", default="./videos", help="mp4 폴더 (기본 ./videos)")
    p.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    p.add_argument("--dry-run", action="store_true", help="업로드 없이 CSV 검증만")
    p.add_argument("--client-secret", default="client_secret.json")
    p.add_argument("--token", default="token.json")
    p.add_argument("--limit", type=int, default=0, help="이번 실행에서 최대 N개만 업로드 (0=전부)")
    return p.parse_args()


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in CSV_FIELDS:
            r.setdefault(k, "")
            r[k] = (r[k] or "").strip()
    return rows


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def validate(row, video_dir, privacy):
    """(경고목록, 오류목록) 반환. 오류가 있으면 그 행은 건너뛴다."""
    warns, errs = [], []
    if not row["file"]:
        errs.append("file 비어 있음")
    elif not os.path.isfile(os.path.join(video_dir, row["file"])):
        warns.append(f"파일 없음: {os.path.join(video_dir, row['file'])}")
    if not row["title"]:
        errs.append("title 비어 있음")
    elif len(row["title"]) > 100:
        errs.append("title 100자 초과")
    if row["publish_at"] and privacy != "private":
        errs.append("publish_at 지정 시 --privacy 는 private 이어야 함")
    return warns, errs


def get_service(client_secret, token_path):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[인증] 토큰 갱신 중...")
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secret):
                sys.exit(f"[오류] {client_secret} 이 없습니다. Google Cloud 콘솔에서 OAuth 클라이언트를 내려받아 두세요.")
            print("[인증] 브라우저에서 Google 로그인 창이 열립니다...")
            flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print(f"[인증] 토큰 저장: {token_path}")
    return build("youtube", "v3", credentials=creds)


def build_body(row, privacy):
    tags = [t.strip() for t in row["tags"].split(";") if t.strip()]
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}
    if row["publish_at"]:
        status["publishAt"] = row["publish_at"]
    return {
        "snippet": {
            "title": row["title"],
            "description": row["description"],
            "tags": tags,
            "categoryId": "27",
            "defaultLanguage": "ko",
        },
        "status": status,
    }


def upload_one(youtube, path, body):
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            media = MediaFileUpload(path, chunksize=CHUNK_SIZE, resumable=True)
            req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            resp = None
            while resp is None:
                st, resp = req.next_chunk()
                if st:
                    print(f"    진행 {int(st.progress() * 100)}%")
            return resp["id"]
        except HttpError as e:
            if e.resp.status >= 500 and attempt < MAX_RETRIES:
                wait = 2 ** attempt
                print(f"    서버 오류 {e.resp.status}, {wait}초 후 재시도 ({attempt}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            raise


def main():
    a = parse_args()
    if not os.path.isfile(a.csv):
        sys.exit(f"[오류] CSV 없음: {a.csv}")
    rows = read_csv(a.csv)
    print(f"[시작] CSV {a.csv} ({len(rows)}행), 폴더 {a.dir}, 공개설정 {a.privacy}"
          + (", DRY-RUN" if a.dry_run else ""))

    results = []  # (file, video_id, url, result)
    youtube = None
    done = 0
    for i, row in enumerate(rows, 1):
        name = row["file"] or f"(행 {i})"
        if row["status"] == "uploaded":
            print(f"[{i}] {name}: 이미 업로드됨, 건너뜀 ({row['video_id']})")
            results.append((name, row["video_id"], row["url"], "skip"))
            continue
        if a.limit and done >= a.limit:
            print(f"[{i}] {name}: --limit {a.limit} 도달, 건너뜀")
            results.append((name, "", "", "skip"))
            continue

        warns, errs = validate(row, a.dir, a.privacy)
        for w in warns:
            print(f"[{i}] {name}: 경고 - {w}")
        if errs:
            for e in errs:
                print(f"[{i}] {name}: 오류 - {e}")
            results.append((name, "", "", "fail"))
            continue

        body = build_body(row, a.privacy)
        if a.dry_run:
            sched = f", 예약 {row['publish_at']}" if row["publish_at"] else ""
            print(f"[{i}] {name}: 업로드 예정 - 제목 '{row['title']}', 태그 {body['snippet']['tags']}{sched}")
            results.append((name, "", "", "dry-run" if not warns else "dry-run(파일없음)"))
            done += 1
            continue
        if warns:  # 실제 실행에서 파일이 없으면 업로드 불가
            results.append((name, "", "", "fail"))
            continue

        if youtube is None:
            youtube = get_service(a.client_secret, a.token)
        path = os.path.join(a.dir, row["file"])
        print(f"[{i}] {name}: 업로드 시작 ({os.path.getsize(path) // (1024 * 1024)}MB)")
        try:
            vid = upload_one(youtube, path, body)
            url = f"https://youtu.be/{vid}"
            row["status"], row["video_id"], row["url"] = "uploaded", vid, url
            write_csv(a.csv, rows)
            print(f"[{i}] {name}: 완료 {url}")
            results.append((name, vid, url, "ok"))
        except Exception as e:  # noqa: BLE001 - 한 편 실패해도 나머지는 계속
            print(f"[{i}] {name}: 실패 - {e}")
            results.append((name, "", "", "fail"))
        done += 1
        time.sleep(2)

    print("\n== 결과 요약 ==")
    print(f"{'file':<32} {'video_id':<14} {'url':<30} result")
    for f, v, u, r in results:
        print(f"{f:<32} {v:<14} {u:<30} {r}")
    failed = sum(1 for r in results if r[3] == "fail")
    print(f"\n총 {len(results)}행, 실패 {failed}건")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
