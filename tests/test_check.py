"""Self-check for check.py against two local fixture sites (good and bad).

    python3 tests/test_check.py

Serves each fixture with http.server on a free port and asserts the codes
that must PASS or FAIL. No network. Redirect and alias-host checks (A1/A2)
are host-level and are exercised only on real sites.
"""
import http.server
import json
import os
import socketserver
import subprocess
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "..", "skills", "agent-visible-site", "scripts", "check.py")

PERSON = {
    "@context": "https://schema.org",
    "@graph": [{
        "@type": "Person", "@id": "http://localhost/#person", "name": "Jane Doe",
        "description": "Jane Doe — engineer. 10 years; ex-A, B; staff engineer at C.",
        "worksFor": {"@type": "Organization", "name": "C"}, "knowsAbout": ["x", "y"],
        "sameAs": ["https://github.com/j", "https://x.com/j", "https://linkedin.com/in/j", "https://blog.j", "https://t.me/j"],
    }, {"@type": "ProfilePage", "dateModified": "2026-09-01", "mainEntity": {"@id": "http://localhost/#person"}}],
}

def page(title, body, ld=None, desc=""):
    ld_tag = f'<script type="application/ld+json">{json.dumps(ld)}</script>' if ld else ""
    return f"""<!doctype html><html><head><title>{title}</title>
<meta name="description" content="{desc}"><meta property="og:description" content="{desc}">{ld_tag}</head>
<body><h1>{title}</h1><p>{body}</p></body></html>"""

FILLER = "Plain readable text. " * 40

GOOD = {
    "index.html": page("Jane Doe", FILLER, {"@context": "https://schema.org", "@graph": PERSON["@graph"][:1]}, PERSON["@graph"][0]["description"]),
    "about/index.html": page("About Jane Doe", "Jane Doe is an engineer based in City. Staff engineer at C since 2024. Ex-A (2019–2021), ex-B (2021–2024). Updated 2026-09-01. " + FILLER, PERSON, ""),
    "robots.txt": "User-agent: *\nAllow: /\nContent-Signal: search=yes\nSitemap: /sitemap.xml\n",
    "sitemap.xml": "<urlset><url><loc>{o}/</loc><lastmod>2026-09-01</lastmod></url><url><loc>{o}/about</loc><lastmod>2026-08-01</lastmod></url><url><loc>{o}/notes</loc><lastmod>2026-07-01</lastmod></url></urlset>",
    "notes/index.html": page("Notes", FILLER),
    "llms.txt": "# Jane Doe\n\n> Jane Doe is an engineer based in City.\n\nWhen to use this: bio.\n\n## About\n\n- [About](" + "{o}" + "/about): bio\n",
}

BAD = {
    "index.html": page("Jane's Site", "<script>renderApp()</script>", None, "Senior engineer, ex-Google"),
    "robots.txt": "User-agent: OAI-SearchBot\nDisallow: /\nUser-agent: *\nAllow: /\n",
    "sitemap.xml": "<urlset><url><loc>{o}/</loc><lastmod>2026-09-04</lastmod></url><url><loc>{o}/x</loc><lastmod>2026-09-04</lastmod></url></urlset>",
    "x/index.html": page("Jane's Site", "short"),
}


class _Handler(http.server.BaseHTTPRequestHandler):
    """Static files like a real host: /x -> x/index.html, no trailing-slash
    redirects, content-type by extension. Unknown path: 404 page (GOOD) or the
    homepage with status 200 (BAD, a soft 404)."""
    root = ""
    soft404 = False

    def do_GET(self):
        path = self.path.split("?")[0].strip("/")
        candidates = [path, path + "/index.html", (path or "index") + ".html"] if path else ["index.html"]
        for c in candidates:
            full = os.path.join(self.root, c)
            if os.path.isfile(full):
                return self._send(200, full)
        if self.soft404:
            return self._send(200, os.path.join(self.root, "index.html"))
        body = b"<!doctype html><html><body><h1>Not found</h1><p>Try <a href=\"/\">home</a> or <a href=\"/about\">about</a>.</p></body></html>"
        self.send_response(404)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def _send(self, status, full):
        ext = full.rsplit(".", 1)[-1]
        ct = {"html": "text/html", "txt": "text/plain", "xml": "application/xml"}.get(ext, "application/octet-stream")
        with open(full, "rb") as f:
            body = f.read()
        self.send_response(status)
        self.send_header("Content-Type", ct)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def serve(files, soft404):
    d = tempfile.mkdtemp()
    _Handler.root, _Handler.soft404 = d, soft404
    srv = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    origin = f"http://127.0.0.1:{srv.server_address[1]}"
    for name, body in files.items():
        path = os.path.join(d, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(body.replace("{o}", origin))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return origin, srv


def run(origin, name):
    out = subprocess.run([sys.executable, CHECK, origin, "--name", name, "--json"], capture_output=True, text=True)
    assert out.returncode in (0, 1), out.stderr
    return {r["check"] + ":" + r["status"] for r in json.loads(out.stdout)["results"]}


def main():
    origin, srv = serve(GOOD, soft404=False)
    got = run(origin, "Jane Doe")
    srv.shutdown()
    for code in ["A3", "A4", "B1", "B2", "C1", "C2", "C3", "D1", "D2", "E1", "E2", "F1", "F2", "G1"]:
        assert f"{code}:PASS" in got, f"GOOD site should pass {code}; got {sorted(got)}"

    origin, srv = serve(BAD, soft404=True)
    got = run(origin, "Jane Doe")
    srv.shutdown()
    for code in ["A3", "A4", "B2", "C1", "C2", "D1", "E1", "F1", "G2"]:
        assert f"{code}:FAIL" in got, f"BAD site should fail {code}; got {sorted(got)}"
    print("ok")


if __name__ == "__main__":
    main()
