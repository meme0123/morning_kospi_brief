#!/usr/bin/env python3
import html

REQUIRED_SECTIONS = {"summary", "macro", "scenarios", "news", "risk"}
TONE_CLASSES = {"bull", "neutral", "bear"}
SCENARIO_CLASSES = {"base", "bull", "bear"}


class ReportDataError(ValueError):
    pass


def require_object(value, name):
    if not isinstance(value, dict):
        raise ReportDataError(f"{name} must be an object")
    return value


def require_list(value, name, minimum=1, maximum=None):
    if not isinstance(value, list) or len(value) < minimum:
        raise ReportDataError(f"{name} must contain at least {minimum} items")
    if maximum is not None and len(value) > maximum:
        raise ReportDataError(f"{name} must contain at most {maximum} items")
    return value


def require_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ReportDataError(f"{name} must be a non-empty string")
    return value.strip()


def require_probability(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise ReportDataError(f"{name} must be an integer from 0 to 100")
    return value


def escaped(value):
    return html.escape(str(value), quote=True)


def tone_class(value, name):
    tone = require_text(value, name)
    if tone not in TONE_CLASSES:
        raise ReportDataError(f"{name} must be one of {', '.join(sorted(TONE_CLASSES))}")
    return tone


def value_tone_class(value):
    return {"bull": "up", "neutral": "muted", "bear": "down"}[value]


def validate_report(data):
    report = require_object(data, "report")
    if set(report) != REQUIRED_SECTIONS:
        missing = REQUIRED_SECTIONS - set(report)
        unexpected = set(report) - REQUIRED_SECTIONS
        raise ReportDataError(
            f"report sections mismatch (missing: {sorted(missing)}, "
            f"unexpected: {sorted(unexpected)})"
        )

    summary = require_object(report["summary"], "summary")
    require_text(summary.get("audio_summary"), "summary.audio_summary")
    if len(summary["audio_summary"]) < 250 or len(summary["audio_summary"]) > 350:
        raise ReportDataError("summary.audio_summary must be 250–350 characters")
    tickers = require_list(summary.get("tickers"), "summary.tickers", 6, 6)
    for number, ticker in enumerate(tickers, 1):
        ticker = require_object(ticker, f"summary.tickers[{number}]")
        for field in ("label", "value"):
            require_text(ticker.get(field), f"summary.tickers[{number}].{field}")
        if len(ticker["label"]) + len(ticker["value"]) > 30:
            raise ReportDataError(f"summary.tickers[{number}] must be at most 30 characters")
        tone_class(ticker.get("tone"), f"summary.tickers[{number}].tone")

    indices = require_object(summary.get("indices"), "summary.indices")
    if set(indices) != {"kospi", "kosdaq"}:
        raise ReportDataError("summary.indices must contain kospi and kosdaq")
    for market in ("kospi", "kosdaq"):
        index = require_object(indices[market], f"summary.indices.{market}")
        probabilities = require_object(
            index.get("probabilities"), f"summary.indices.{market}.probabilities"
        )
        if set(probabilities) != {"up", "flat", "down"}:
            raise ReportDataError(f"{market} probabilities need up, flat, and down")
        for key, value in probabilities.items():
            require_probability(value, f"{market}.probabilities.{key}")
        if sum(probabilities.values()) != 100:
            raise ReportDataError(f"{market} probabilities must total 100")
        tone_class(index.get("tone"), f"{market}.tone")
        for field in ("status", "gap", "stance", "support", "resistance"):
            require_text(index.get(field), f"{market}.{field}")

    drivers = require_list(summary.get("drivers"), "summary.drivers", 3, 3)
    for number, driver in enumerate(drivers, 1):
        driver = require_object(driver, f"summary.drivers[{number}]")
        tone_class(driver.get("tone"), f"summary.drivers[{number}].tone")
        for field in ("label", "impact", "title", "description"):
            require_text(driver.get(field), f"summary.drivers[{number}].{field}")
        tags = require_list(driver.get("tags"), f"summary.drivers[{number}].tags", 1, 4)
        for tag_number, tag in enumerate(tags, 1):
            require_text(tag, f"summary.drivers[{number}].tags[{tag_number}]")

    macro = require_object(report["macro"], "macro")
    require_list(macro.get("rows"), "macro.rows", 6, 12)
    for number, row in enumerate(macro["rows"], 1):
        row = require_object(row, f"macro.rows[{number}]")
        tone_class(row.get("change_tone"), f"macro.rows[{number}].change_tone")
        tone_class(row.get("impact_tone"), f"macro.rows[{number}].impact_tone")
        for field in ("name", "value", "change", "signal", "impact"):
            require_text(row.get(field), f"macro.rows[{number}].{field}")

    scenarios = require_object(report["scenarios"], "scenarios")
    scenario_items = require_list(scenarios.get("items"), "scenarios.items", 3, 3)
    scenario_types = set()
    for number, item in enumerate(scenario_items, 1):
        item = require_object(item, f"scenarios.items[{number}]")
        scenario_type = require_text(item.get("type"), f"scenarios.items[{number}].type")
        if scenario_type not in SCENARIO_CLASSES:
            raise ReportDataError(f"invalid scenario type: {scenario_type}")
        scenario_types.add(scenario_type)
        require_probability(item.get("probability"), f"scenarios.items[{number}].probability")
        require_text(item.get("title"), f"scenarios.items[{number}].title")
        require_text(item.get("headline"), f"scenarios.items[{number}].headline")
        details = require_list(item.get("details"), f"scenarios.items[{number}].details", 2, 4)
        for detail_number, detail in enumerate(details, 1):
            require_text(detail, f"scenarios.items[{number}].details[{detail_number}]")
    if scenario_types != SCENARIO_CLASSES:
        raise ReportDataError("scenarios must include base, bull, and bear")
    if sum(item["probability"] for item in scenario_items) != 100:
        raise ReportDataError("scenario probabilities must total 100")
    require_list(scenarios.get("flow_triggers"), "scenarios.flow_triggers", 3, 3)
    for number, trigger in enumerate(scenarios["flow_triggers"], 1):
        trigger = require_object(trigger, f"scenarios.flow_triggers[{number}]")
        require_text(trigger.get("label"), f"flow_triggers[{number}].label")
        require_text(trigger.get("detail"), f"flow_triggers[{number}].detail")

    news = require_object(report["news"], "news")
    news_items = require_list(news.get("items"), "news.items", 1, 3)
    for number, item in enumerate(news_items, 1):
        item = require_object(item, f"news.items[{number}]")
        for field in ("title", "summary", "short_term", "long_term"):
            require_text(item.get(field), f"news.items[{number}].{field}")

    risk = require_object(report["risk"], "risk")
    require_text(risk.get("cash_guidance"), "risk.cash_guidance")
    for field in ("monitoring", "position_triggers"):
        entries = require_list(risk.get(field), f"risk.{field}", 2, 5)
        for number, item in enumerate(entries, 1):
            item = require_object(item, f"risk.{field}[{number}]")
            require_text(item.get("label"), f"risk.{field}[{number}].label")
            require_text(item.get("detail"), f"risk.{field}[{number}].detail")
    return report


def render_ticker(label, value, tone="neutral"):
    return (
        '<div class="ticker-item">'
        f"<span>{escaped(label)}</span> <span class=\"{value_tone_class(tone)}-val\">"
        f"{escaped(value)}</span></div>"
    )


def render_index_card(name, index):
    probabilities = index["probabilities"]
    title = "코스피 (KOSPI)" if name == "kospi" else "코스닥 (KOSDAQ)"
    labels = (("up", "상승"), ("flat", "보합"), ("down", "하락"))
    probability_labels = "".join(
        f"<span>{label} {probabilities[key]}%</span>" for key, label in labels
    )
    probability_segments = "".join(
        f'<div class="prob-segment prob-{key}" style="width: {probabilities[key]}%;"></div>'
        for key, _ in labels
    )
    metrics = (
        ("예상 시초가 갭", index["gap"]),
        ("스윙 권고 Stance", index["stance"]),
        ("단기 지지선 (Support)", index["support"]),
        ("상단 저항선 (Resistance)", index["resistance"]),
    )
    metric_html = "".join(
        '<div class="metric-box">'
        f'<div class="metric-label">{escaped(label)}</div>'
        f'<div class="metric-value">{escaped(value)}</div>'
        "</div>"
        for label, value in metrics
    )
    return f"""
      <div class="card">
        <div class="card-header-flex">
          <div>
            <span class="index-board">{'MAIN BOARD BENCHMARK' if name == 'kospi' else 'GROWTH & TECH BOARD'}</span>
            <h3 class="index-title">{title} 방향성 확률</h3>
          </div>
          <span class="badge-status badge-{tone_class(index['tone'], name + '.tone')}">{escaped(index['status'])}</span>
        </div>
        <div class="prob-bar-wrap">
          <div class="prob-bar-label">{probability_labels}</div>
          <div class="prob-progress">{probability_segments}</div>
        </div>
        <div class="metric-rows">{metric_html}</div>
      </div>"""


def render_driver(driver):
    tags = "".join(f'<span class="sector-tag">{escaped(tag)}</span>' for tag in driver["tags"])
    impact_tone = tone_class(driver["tone"], "driver.tone")
    return f"""
      <div class="card driver-card">
        <div>
          <div class="driver-meta">
            <span class="badge-status badge-{tone_class(driver['tone'], 'driver.tone')}">{escaped(driver['label'])}</span>
            <span class="impact-tag impact-{impact_tone}">{escaped(driver['impact'])}</span>
          </div>
          <h4 class="driver-title">{escaped(driver['title'])}</h4>
          <p class="driver-desc">{escaped(driver['description'])}</p>
        </div>
        <div class="tag-container">{tags}</div>
      </div>"""


def render_macro_row(row):
    change_class = value_tone_class(row["change_tone"])
    return (
        "<tr>"
        f"<td><strong>{escaped(row['name'])}</strong></td>"
        f"<td>{escaped(row['value'])}</td>"
        f'<td><span class="{change_class}-val">'
        f"{escaped(row['change'])}</span></td>"
        f"<td>{escaped(row['signal'])}</td>"
        f'<td><span class="badge-status badge-{tone_class(row["impact_tone"], "macro.impact_tone")}">'
        f"{escaped(row['impact'])}</span></td>"
        "</tr>"
    )


def render_scenario(item):
    details = "".join(f"<li>{escaped(detail)}</li>" for detail in item["details"])
    return f"""
      <div class="card scenario-card {item['type']}">
        <div class="card-header-flex">
          <span class="scenario-title">{escaped(item['title'])}</span>
          <span class="scenario-prob {item['type']}">{item['probability']}%</span>
        </div>
        <p class="scenario-headline"><strong>“{escaped(item['headline'])}”</strong></p>
        <ul class="scenario-points">{details}</ul>
      </div>"""


def render_flow_trigger(item):
    return (
        '<div class="flow-trigger">'
        f'<span class="flow-trigger-label">{escaped(item["label"])}</span>'
        f"<br>{escaped(item['detail'])}</div>"
    )


def render_news(item, number):
    return f"""
      <div class="news-card">
        <h4 class="news-title">{number}. {escaped(item['title'])}</h4>
        <p class="news-summary">{escaped(item['summary'])}</p>
        <div class="news-split-grid">
          <div class="split-col">
            <h5>단기 영향 (1~3 Days)</h5>
            <p>{escaped(item['short_term'])}</p>
          </div>
          <div class="split-col">
            <h5>스윙/중장기 관점 (1~3 Months)</h5>
            <p>{escaped(item['long_term'])}</p>
          </div>
        </div>
      </div>"""


def render_risk_list(items):
    return "".join(
        f"<li><strong>{escaped(item['label'])}:</strong> {escaped(item['detail'])}</li>"
        for item in items
    )


def render_report(report, report_date):
    summary = report["summary"]
    indices = summary["indices"]
    ticker_items = "".join(
        render_ticker(item["label"], item["value"], item["tone"])
        for item in summary["tickers"]
    )

    index_cards = render_index_card("kospi", indices["kospi"]) + render_index_card(
        "kosdaq", indices["kosdaq"]
    )
    driver_cards = "".join(render_driver(item) for item in summary["drivers"])
    macro_rows = "".join(render_macro_row(row) for row in report["macro"]["rows"])
    scenarios = report["scenarios"]
    scenario_cards = "".join(render_scenario(item) for item in scenarios["items"])
    flow_triggers = "".join(
        render_flow_trigger(item) for item in scenarios["flow_triggers"]
    )
    news_cards = "".join(
        render_news(item, number)
        for number, item in enumerate(report["news"]["items"], 1)
    )
    risk = report["risk"]
    return f"""
  <div class="sub-meta-header">
    <div class="meta-date-info">
      <strong>{escaped(report_date)}</strong>
      <span class="meta-badge">개장 전 전략 브리핑 · 07:00 KST 배포</span>
    </div>
    <div class="ticker-tape">{ticker_items}</div>
  </div>
  <main class="container">
    <section id="summary" class="report-section">
      <div class="section-title">
        <span>Part 1. 1분 핵심 요약 (Executive Summary)</span>
        <span class="section-subtitle">정량 확률 모델 및 개장 전 종합 포지셔닝 가이드</span>
      </div>
      <p id="audio-summary">{escaped(summary['audio_summary'])}</p>
      <div class="grid-2">{index_cards}</div>
      <div class="grid-3">{driver_cards}</div>
    </section>

    <section id="macro" class="report-section">
      <div class="section-title">
        <span>Part 2-1. 글로벌 선행지표 대시보드 (Global Leading Indicators)</span>
        <span class="section-subtitle">간밤 마감 및 선행 지표 퀀트 요약</span>
      </div>
      <div class="card table-card">
        <table class="macro-table">
          <thead><tr><th>지표명</th><th>종가 / 현재가</th><th>등락폭 / 등락률</th><th>선행 함의 (Signal)</th><th>국내 증시 영향도</th></tr></thead>
          <tbody>{macro_rows}</tbody>
        </table>
      </div>
    </section>

    <section id="scenarios" class="report-section">
      <div class="section-title">
        <span>Part 2-2. 지수별 장중 시나리오 및 수급 변곡점 (Scenario Matrix)</span>
        <span class="section-subtitle">수급 트리거에 따른 대응 시나리오</span>
      </div>
      <div class="grid-3">{scenario_cards}</div>
      <div class="card flow-trigger-card">
        <h4>⚡ 당일 수급 방향성 판단의 핵심 변곡점 (Quant Triggers)</h4>
        <div class="flow-trigger-grid">{flow_triggers}</div>
      </div>
    </section>

    <section id="news" class="report-section">
      <div class="section-title">
        <span>Part 2-3. 중장기 펀더멘털 브리핑 (Macro &amp; Industry Deep Dive)</span>
        <span class="section-subtitle">단기 노이즈를 걷어낸 본질적 체력 평가</span>
      </div>
      {news_cards}
    </section>

    <section id="risk" class="report-section">
      <div class="section-title">
        <span>Part 2-4. 리스크 관리 가이드 (Risk Management Guide)</span>
        <span class="section-subtitle">손실 제한 및 포트폴리오 보존 원칙</span>
      </div>
      <div class="grid-2">
        <div class="card">
          <h4 class="risk-card-title monitoring">🔍 장중 실시간 모니터링 체크포인트</h4>
          <ol class="risk-list">{render_risk_list(risk['monitoring'])}</ol>
        </div>
        <div class="card">
          <h4 class="risk-card-title triggers">🚨 스윙 포지션 비중 축소 트리거 (Stop-loss Rule)</h4>
          <ul class="risk-list">{render_risk_list(risk['position_triggers'])}</ul>
        </div>
      </div>
      <div class="risk-banner">
        <h4>💡 오늘의 현금 비중 및 운용 가이드</h4>
        <p>{escaped(risk['cash_guidance'])}</p>
      </div>
    </section>
  </main>"""
