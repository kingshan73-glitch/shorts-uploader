# Shorts Batch Uploader

로컬 폴더의 세로형 짧은 영상(mp4)을 CSV 메타데이터로 **본인 채널**에 일괄 업로드하는 개인용 CLI.
YouTube Data API v3 사용, 요청 범위는 `youtube.upload` 하나.

- 홈페이지 / 개인정보처리방침 / 약관: https://kingshan73-glitch.github.io/shorts-uploader/ (`docs/`)

## 설치

```
pip install -r requirements.txt
```

## 준비

1. Google Cloud 콘솔에서 YouTube Data API v3 를 켜고, OAuth 클라이언트(데스크톱 앱)를 만든 뒤
   `client_secret.json` 을 내려받아 **스크립트 옆에** 둔다.
2. `videos.sample.csv` 를 복사해 `videos.csv` 를 만들고 채운다.
   - `file` 파일명 (`--dir` 폴더 기준, 기본 `./videos`)
   - `title` (100자 이내), `description`, `tags` (세미콜론 `;` 구분)
   - `publish_at` 예약 공개 시각, ISO-8601 (`2026-09-10T09:00:00+09:00`). 지정하면 `--privacy private` 이어야 한다.
   - `status`, `video_id`, `url` 은 비워 둔다. 성공하면 스크립트가 `uploaded` 와 ID, URL 을 채우며, 이미 `uploaded` 인 행은 건너뛴다.
3. 영상을 `videos/` 폴더에 넣는다.

## 실행

```
python upload_shorts.py --dry-run          # CSV 검증만, 인증/네트워크 없음
python upload_shorts.py                    # 실제 업로드 (첫 실행 시 브라우저 로그인, token.json 저장)
python upload_shorts.py --privacy unlisted --limit 3
```

옵션: `--csv`, `--dir`, `--privacy private|unlisted|public`, `--client-secret`, `--token`, `--limit N`, `--dry-run`

## 주의

- Google Cloud 프로젝트가 **YouTube API 감사(compliance audit)를 통과하기 전**에는 이 API 로 올린 영상이
  **비공개(private)로 잠깁니다.** 통과 후에는 `--privacy` 로 공개 설정을 바꿀 수 있습니다.
- 인증 정보는 PC 의 `token.json` 에만 저장됩니다. 권한 철회는 https://security.google.com/settings/security/permissions 에서,
  파일 삭제로도 완전히 제거됩니다.
- `client_secret*.json`, `token.json`, `videos/`, `*.mp4` 는 `.gitignore` 로 제외돼 있습니다.
