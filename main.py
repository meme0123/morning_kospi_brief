#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from google import genai
from google.genai import types

from report_renderer import ReportDataError, render_report, validate_report

KST = ZoneInfo("Asia/Seoul")
MODEL = "gemini-3.8-flash"


def fail(message):
    print(message)
    sys.exit(1)


def load_text_file(path):
    if not os.path.exists(path):
        fail(f"[오류] {path} 파일이 없습니다.")
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def main():
    system_instruction = load_text_file("prompt.txt")
    html_template = load_text_file("dashboard_template.html")
    if html_template.count("{{REPORT_CONTENT}}") != 1 or html_template.count(
        "{{REPORT_DATE}}"
    ) != 1:
        fail("[오류] dashboard_template.html의 치환 표식이 올바르지 않습니다.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        fail("[오류] GEMINI_API_KEY가 설정되지 않았습니다.")

    now = datetime.now(KST)
    weekdays = ("월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일")
    report_date = f"{now:%Y-%m-%d} ({weekdays[now.weekday()]})"
    user_query = (
        f"오늘은 {now.strftime('%Y년 %m월 %d일')}입니다. "
        "개장 전 국내 증시 브리핑에 필요한 데이터 객체만 JSON으로 작성하세요. "
        "HTML이나 Markdown은 출력하지 마세요."
    )
    print(f"[{now.strftime('%H:%M:%S')}] 최신 마켓 데이터 분석 및 대시보드 생성 중...")

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
    except Exception as error:
        fail(f"[호출 실패] 오류: {error}")

    usage = getattr(response, "usage_metadata", None)
    if usage is not None:
        print(
            "[토큰 사용량] "
            f"입력 {getattr(usage, 'prompt_token_count', '확인 불가')} / "
            f"출력 {getattr(usage, 'candidates_token_count', '확인 불가')} / "
            f"합계 {getattr(usage, 'total_token_count', '확인 불가')}"
        )
    else:
        print("[토큰 사용량] API 응답에 usage 메타데이터가 없습니다.")

    if not response.text:
        fail("[생성 실패] 모델이 JSON 데이터를 반환하지 않았습니다.")
    try:
        report = validate_report(json.loads(response.text))
    except (json.JSONDecodeError, ReportDataError) as error:
        fail(f"[생성 실패] 보고서 데이터 형식이 올바르지 않습니다: {error}")

    report_content = render_report(report, report_date)
    html_code = (
        html_template.replace("{{REPORT_CONTENT}}", report_content)
        .replace("{{REPORT_DATE}}", now.strftime("%Y년 %m월 %d일"))
    )
    filename = f"dashboard_{now.strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_code)

    print(f"[{datetime.now(KST).strftime('%H:%M:%S')}] 대시보드 생성 완료: {filename}")
    print(f"👉 브라우저로 확인: explorer.exe {filename}")


if __name__ == "__main__":
    main()
