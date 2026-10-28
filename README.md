# morning_kospi_brief

The report generator keeps its visual design in `dashboard_template.html`. Gemini returns validated JSON market data only; `main.py` escapes those values and renders them into fixed HTML structures. The model never writes HTML or CSS, so report data can change without changing the dashboard layout.

Run `python main.py` from this directory after setting `GEMINI_API_KEY`. Update shared styling in `dashboard_template.html`, the fixed report rendering in `main.py`, and market-data guidance/schema in `prompt.txt`. Google Search is not enabled by the generator.
