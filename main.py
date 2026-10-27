#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from google import genai
from google.genai import types
import markdown

def main():
    prompt_file_path = "prompt.txt"
    
    # 1. prompt.txt 파일 존재 확인 및 읽기
    if not os.path.exists(prompt_file_path):
        print(f"[오류] '{prompt_file_path}' 파일을 찾을 수 없습니다.")
        sys.exit(1)

    with open(prompt_file_path, "r", encoding="utf-8") as f:
        system_instruction = f.read()

    # 2. API Key 확인
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[오류] GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("터미널에 'export GEMINI_API_KEY=\"your_key\"'를 실행해주세요.")
        sys.exit(1)
    print(f"api_key: {api_key[:4]}****{api_key[-4:]}")

    # 3. Gemini 클라이언트 초기화
    client = genai.Client(api_key=api_key)

    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    user_query = f"""
    오늘은 {today_str}입니다.
    제공된 시스템 가이드라인(Role, Context, Constraint, Output Structure)에 맞추어
    오늘 정규장 개장 전 국내 증시(코스피/코스닥) 분석 리포트를 작성해주세요.
    간밤의 최신 미국 증시 결과, 금리, 환율, 주요 뉴스를 검색하여 정확한 데이터를 반영하십시오.
    """

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 최신 마켓 데이터 검색 및 리포트 생성 중...")

    # 4. 모델 호출 (실시간 구글 검색 도구 탑재)
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                # 실시간 간밤 해외 지표 및 뉴스를 검색하도록 설정
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,  # 사실 기반 분석을 위해 낮은 온도값 권장
            ),
        )
    except Exception as e:
        print(f"[호출 실패] API 요청 중 오류가 발생했습니다: {e}")
        sys.exit(1)

    md_content = response.text
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 리포트 생성 완료. HTML 변환 중...")

    # 5. 마크다운 -> HTML 변환 (표, 코드블록 지원 확장자 포함)
    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "nl2br"]
    )

    # 6. 보고서용 모던 반응형 CSS 템플릿
    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[{today_str}] 코스피·코스닥 개장 전 전략 리포트</title>
    <style>
        :root {{
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-sub: #64748b;
            --primary: #2563eb;
            --border: #e2e8f0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Pretendard", sans-serif;
            line-height: 1.65;
            color: var(--text-main);
            background-color: var(--bg-color);
            margin: 0;
            padding: 30px 15px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: var(--card-bg);
            padding: 40px;
            border-radius: 14px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border: 1px solid var(--border);
        }}
        h1 {{
            color: #0f172a;
            border-bottom: 2px solid var(--primary);
            padding-bottom: 12px;
            font-size: 1.8rem;
        }}
        h2 {{
            color: #1e3a8a;
            margin-top: 35px;
            border-left: 5px solid var(--primary);
            padding-left: 12px;
            font-size: 1.4rem;
        }}
        h3 {{
            color: #334155;
            margin-top: 25px;
            font-size: 1.15rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95rem;
        }}
        th, td {{
            border: 1px solid var(--border);
            padding: 12px 14px;
            text-align: left;
        }}
        th {{
            background-color: #f1f5f9;
            color: #0f172a;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        ul, ol {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 6px;
        }}
        hr {{
            border: 0;
            height: 1px;
            background: var(--border);
            margin: 30px 0;
        }}
        blockquote {{
            margin: 20px 0;
            padding: 12px 20px;
            background-color: #f1f5f9;
            border-left: 4px solid #94a3b8;
            font-size: 0.9rem;
            color: var(--text-sub);
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>
"""

    # 7. 파일 저장
    output_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 생성 완료: {output_filename}")
    print(f"👉 윈도우 브라우저에서 바로 열기: explorer.exe {output_filename}")

if __name__ == "__main__":
    main()