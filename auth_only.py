"""OAuth 인증만 수행해 token.json 을 만든다 (업로드 없음).

감사 신청용 동의 화면 스크린샷을 찍거나, 업로드 전에 미리 로그인해 둘 때 사용.
브라우저를 자동으로 열지 않고 인증 URL 을 출력한다.
"""
import argparse
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-secret", default="client_secret.json")
    ap.add_argument("--token", default="token.json")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()

    flow = InstalledAppFlow.from_client_secrets_file(args.client_secret, SCOPES)
    creds = flow.run_local_server(
        port=args.port,
        open_browser=False,
        authorization_prompt_message="[인증 URL] {url}",
        success_message="인증 완료. 이 창은 닫아도 됩니다.",
    )
    with open(args.token, "w", encoding="utf-8") as f:
        f.write(creds.to_json())
    print(f"[완료] 토큰 저장: {args.token}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
