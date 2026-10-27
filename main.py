#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai
from google.genai import types

KST = ZoneInfo("Asia/Seoul")

def main():
    # 1. prompt.txt 읽기
    if not os.path.exists("prompt.txt"):
        print("[오류] prompt.txt 파일이 없습니다.")
        sys.exit(1)

    with open("prompt.txt", "r", encoding="utf-8") as f:
        system_instruction = f.read()

    # 2. 클라이언트 초기화
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[오류] GEMINI_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    today_str = datetime.now(KST).strftime("%Y년 %m월 %d일")

    user_query = f"""
    오늘은 {today_str}입니다.
    지침서(prompt.txt)의 디자인 및 레이아웃 규격에 맞추어, 
    간밤의 최신 글로벌 시장 데이터를 검색해 완성된 핀테크 대시보드 HTML 파일 전체를 작성해주세요.
    """

    print(f"[{datetime.now(KST).strftime('%H:%M:%S')}] 최신 마켓 데이터 검색 및 대시보드 앱 빌드 중...")

    # 3. 모델 호출 (실시간 구글 검색 사용)
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,
            ),
        )
    except Exception as e:
        print(f"[호출 실패] 오류: {e}")
        sys.exit(1)

    # 4. 백틱(```html) 혹시 들어있으면 제거
    html_code = response.text.strip()
    if html_code.startswith("```html"):
        html_code = html_code[7:]
    if html_code.startswith("```"):
        html_code = html_code[3:]
    if html_code.endswith("```"):
        html_code = html_code[:-3]
    html_code = html_code.strip()

    # 5. HTML 파일 저장
    filename = f"dashboard_{datetime.now(KST).strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_code)

    print(f"[{datetime.now(KST).strftime('%H:%M:%S')}] 대시보드 생성 완료: {filename}")
    print(f"👉 브라우저로 확인: explorer.exe {filename}")

if __name__ == "__main__":
    main()