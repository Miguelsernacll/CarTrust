#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app, recommendations  # noqa: E402


OUTPUTS = [
    ROOT / "CarTrust_vista_previa_web.html",
    ROOT / "CarTrust_v4_local.html",
]
DEMO_PROFILE = {
    "usage": "family",
    "budget": "250000000",
    "people": "5",
    "daily_km": "50",
    "charging_access": "home",
    "priority": "safety",
    "preferred_type": "suv",
}


def replace_once(pattern, replacement, text):
    updated, count = re.subn(pattern, lambda _match: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"No se pudo reemplazar: {pattern}")
    return updated


def main():
    with app.app_context():
        preview_data = {
            "profile": DEMO_PROFILE,
            "recommendations": recommendations(DEMO_PROFILE),
        }

    with app.test_client() as client:
        response = client.get("/asesor")
        if response.status_code >= 400:
            raise RuntimeError(f"No se pudo renderizar /asesor: HTTP {response.status_code}")
        html = response.get_data(as_text=True)

    css = (ROOT / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    js = (ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")
    payload = json.dumps(preview_data, ensure_ascii=False)

    preview_bootstrap = f"""
  <script>
    window.CarTrustPreviewData = {payload};
    (() => {{
      const nativeFetch = window.fetch ? window.fetch.bind(window) : null;
      window.fetch = (resource, options = {{}}) => {{
        const url = String(typeof resource === "string" ? resource : resource?.url || "");
        if (url.includes("/api/quiz/recommend")) {{
          let profile = {{}};
          try {{ profile = JSON.parse(options.body || "{{}}"); }} catch (_error) {{}}
          const body = JSON.stringify({{
            profile,
            recommendations: window.CarTrustPreviewData.recommendations,
          }});
          return Promise.resolve(new Response(body, {{
            status: 200,
            headers: {{ "Content-Type": "application/json" }},
          }}));
        }}
        if (url.includes("/api/listings")) {{
          return Promise.resolve(new Response(JSON.stringify(window.CarTrustPreviewData.recommendations), {{
            status: 200,
            headers: {{ "Content-Type": "application/json" }},
          }}));
        }}
        if (nativeFetch) return nativeFetch(resource, options);
        return Promise.reject(new Error("CarTrust static preview cannot fetch this resource."));
      }};
    }})();
  </script>"""

    html = html.replace('href="/static/favicon.svg"', 'href="static/favicon.svg"')
    html = replace_once(
        r'<link rel="stylesheet" href="/static/css/styles\.css\?v=[^"]+">',
        f"<style>\n{css}\n</style>",
        html,
    )
    html = replace_once(
        r'<script src="/static/js/app\.js\?v=[^"]+"></script>',
        f"{preview_bootstrap}\n  <script>\n{js}\n  </script>",
        html,
    )
    html = html.replace('href="/"', 'href="http://127.0.0.1:5057/"')
    html = html.replace('action="/"', 'action="http://127.0.0.1:5057/"')
    html = html.replace('href="/asesor"', 'href="http://127.0.0.1:5057/asesor"')
    html = html.replace('href="/carga"', 'href="http://127.0.0.1:5057/carga"')
    html = html.replace('href="/referencias"', 'href="http://127.0.0.1:5057/referencias"')
    html = html.replace('href="/login"', 'href="http://127.0.0.1:5057/login"')
    html = html.replace('href="/registro"', 'href="http://127.0.0.1:5057/registro"')
    html = re.sub(r'href="/listing/(\d+)"', r'href="http://127.0.0.1:5057/listing/\1"', html)
    html = re.sub(r'src="/static/([^"]+)"', r'src="static/\1"', html)
    html = html.replace(
        "</head>",
        '  <meta name="cartrust-preview" content="static-file">\n</head>',
    )

    for output in OUTPUTS:
        output.write_text(html, encoding="utf-8")
        print(output)


if __name__ == "__main__":
    main()
