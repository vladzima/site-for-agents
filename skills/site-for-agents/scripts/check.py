#!/usr/bin/env python3
"""Scorecard for how well a personal site serves AI agents and answer engines.

    python3 check.py https://example.com [--name "Full Name"] [--pages 30]

Stdlib only. Groups A-G are automated; group H (off-site consistency) is a
manual checklist printed at the end. Each line is PASS / FAIL / INFO with the
evidence, so the reader can act without re-fetching.
"""
import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

# Bots that feed *answers* (search/user-triggered fetch). Data, not code: this
# list changes every few months. Training-only crawlers are a separate choice.
ANSWER_BOTS = [
    "OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User",
    "PerplexityBot", "Perplexity-User", "Googlebot", "Bingbot",
]
UA = "Mozilla/5.0 (compatible; site-for-agents check; +https://github.com/vladzima/site-for-agents)"
MIN_TEXT = 500          # chars of visible text a content page must have without JS
ENTITY_PATHS = ["/about", "/about-me", "/bio", "/cv", "/resume", "/me"]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_ctx = ssl.create_default_context()
_opener = urllib.request.build_opener(_NoRedirect(), urllib.request.HTTPSHandler(context=_ctx))


def fetch(url, accept="text/html,*/*;q=0.8"):
    """(status, headers, body_text). Never follows redirects; never raises."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with _opener.open(req, timeout=20) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:  # DNS, TLS, timeout
        return 0, {}, str(e)


class _Text(HTMLParser):
    """Visible text and first H1, ignoring script/style/noscript."""

    def __init__(self):
        super().__init__()
        self.parts, self.h1, self._skip, self._in_h1 = [], None, 0, False
        self.ld, self._in_ld, self.meta, self.links = [], False, {}, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self._skip += 1
            self._in_ld = tag == "script" and a.get("type") == "application/ld+json"
        elif tag == "h1" and self.h1 is None:
            self._in_h1 = True
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append(a)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = max(0, self._skip - 1)
            self._in_ld = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data):
        if self._in_ld:
            self.ld.append(data)
        elif not self._skip:
            self.parts.append(data)
            if self._in_h1:
                self.h1 = (self.h1 or "") + data


def parse_html(body):
    p = _Text()
    p.feed(body)
    text = re.sub(r"\s+", " ", " ".join(p.parts)).strip()
    nodes = []
    for raw in p.ld:
        try:
            doc = json.loads(raw)
        except ValueError:
            nodes.append({"@type": "__invalid__"})
            continue
        docs = doc if isinstance(doc, list) else [doc]
        for d in docs:
            nodes.extend(d.get("@graph", [d]) if isinstance(d, dict) else [])
    return {"text": text, "h1": (p.h1 or "").strip(), "ld": nodes, "meta": p.meta, "links": p.links}


def person_node(nodes):
    for n in nodes:
        t = n.get("@type")
        if t == "Person" or (isinstance(t, list) and "Person" in t):
            return n
    return None


def parse_robots(body):
    """{agent_lower: [(directive, path)]} in file order."""
    groups, current = {}, []
    for line in body.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        k, v = (s.strip() for s in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            current = [v.lower()]
            for agent in current:
                groups.setdefault(agent, [])
        elif k in ("allow", "disallow"):
            for agent in current:
                groups.setdefault(agent, []).append((k, v))
    return groups


def robots_blocks(groups, bot):
    """True if the bot may not fetch '/' (root disallowed, no allow override)."""
    rules = groups.get(bot.lower(), groups.get("*", []))
    blocked = False
    for directive, path in rules:
        if path in ("/", ""):
            blocked = directive == "disallow" and path == "/"
    return blocked


def sitemap_urls(body):
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body), re.findall(r"<lastmod>\s*([^<\s]+)\s*</lastmod>", body)


def run(origin, name=None, max_pages=30):
    out = []
    ok = lambda code, msg: out.append(("PASS", code, msg))
    no = lambda code, msg: out.append(("FAIL", code, msg))
    info = lambda code, msg: out.append(("INFO", code, msg))
    u = urllib.parse.urlsplit(origin)
    origin = f"{u.scheme}://{u.netloc}"
    host = u.netloc

    # --- A. Reachable ---
    st, hd, body = fetch(origin + "/")
    if 300 <= st < 400 and hd.get("Location"):
        # Given the non-canonical host; check the canonical one, but say so.
        loc = urllib.parse.urlsplit(urllib.parse.urljoin(origin, hd["Location"]))
        info("A1", f"{host}/ redirects to {loc.netloc}; checking {loc.netloc} as the canonical host")
        origin, host = f"{loc.scheme}://{loc.netloc}", loc.netloc
        u = loc
        st, hd, body = fetch(origin + "/")
    if st == 200 and len(body) > MIN_TEXT:
        ok("A1", f"{host}/ serves 200 with {len(body):,} bytes")
    elif 300 <= st < 400:
        no("A1", f"{host}/ redirects again to {hd.get('Location')}; a canonical host must answer 200")
    else:
        no("A1", f"{host}/ returned {st} ({len(body)} bytes)")
    alt = ("www." + host) if not host.startswith("www.") else host[4:]
    st2, hd2, _ = fetch(f"{u.scheme}://{alt}/")
    if 300 <= st2 < 400 and (hd2.get("Location") or "").startswith(origin):
        ok("A2", f"{alt} redirects to {host}")
    elif st2 == 200:
        no("A2", f"{alt} also serves 200: two canonical hosts split the entity; redirect one to the other")
    else:
        info("A2", f"{alt} returned {st2}")
    st, _, robots = fetch(origin + "/robots.txt", accept="text/plain,*/*")
    if st != 200:
        no("A3", f"robots.txt returned {st}; answer bots treat a missing file as allow but Content-Signal cannot be declared")
    else:
        groups = parse_robots(robots)
        blocked = [b for b in ANSWER_BOTS if robots_blocks(groups, b)]
        if blocked:
            no("A3", f"robots.txt blocks answer bots: {', '.join(blocked)}; blocked search bots means no citations")
        else:
            ok("A3", f"robots.txt allows all {len(ANSWER_BOTS)} answer bots")
        info("A3", "Content-Signal declared" if "content-signal" in robots.lower() else "no Content-Signal line (optional rights signal)")
    st, _, _ = fetch(origin + "/__agent_visible_probe__")
    if st in (404, 410):
        ok("A4", f"unknown path returns {st}")
    else:
        no("A4", f"unknown path returns {st}; soft 404s get indexed as real pages")

    # --- B. Readable ---
    st, _, sm = fetch(origin + "/sitemap.xml", accept="application/xml,text/xml,*/*")
    urls, lastmods = ([], [])
    if st == 200 and "<loc>" in sm:
        urls, lastmods = sitemap_urls(sm)
        ok("B1", f"sitemap.xml lists {len(urls)} URLs")
    else:
        no("B1", f"sitemap.xml returned {st} or has no <loc>; agents fall back to link crawling")
    pages = [x for x in urls if x.startswith(origin)][:max_pages] or [origin + "/"]
    parsed, thin = {}, []
    for page in pages:
        st, hd, b = fetch(page)
        ct = hd.get("Content-Type", "")
        if st != 200 or "text/html" not in ct:
            thin.append(f"{urllib.parse.urlsplit(page).path or '/'} ({st} {ct.split(';')[0] or 'no type'})")
            continue
        d = parse_html(b)
        parsed[page] = d
        if not d["h1"] or len(d["text"]) < MIN_TEXT:
            thin.append(f"{urllib.parse.urlsplit(page).path or '/'} (h1={'yes' if d['h1'] else 'no'}, {len(d['text'])} chars)")
    if thin:
        no("B2", f"{len(thin)}/{len(pages)} pages lack an H1 or {MIN_TEXT}+ chars without JS: {'; '.join(thin[:8])}")
    else:
        ok("B2", f"all {len(pages)} sitemap pages have an H1 and {MIN_TEXT}+ chars without JS")

    # --- C. Identifiable ---
    home = parsed.get(origin + "/") or parse_html(fetch(origin + "/")[2])
    entity_url, entity = None, None
    for page, d in parsed.items():
        # A ProfilePage node marks the entity page; prefer one that names this URL.
        pp = [n for n in d["ld"] if n.get("@type") == "ProfilePage"]
        if pp and (entity is None or any(page.rstrip("/") in (n.get("@id", ""), n.get("url", "")) for n in pp)):
            entity_url, entity = page, d
    if entity is None:
        for path in ENTITY_PATHS:
            st, _, b = fetch(origin + path)
            if st == 200:
                entity_url, entity = origin + path, parse_html(b)
                break
    person = person_node((entity or home)["ld"]) or person_node(home["ld"])
    name = name or (person or {}).get("name") or home["meta"].get("author") or ""
    if not name:
        info("C0", "no --name given and no Person JSON-LD or <meta name=author>; name-based checks are weakened")
    if entity is None:
        no("C1", f"no entity page found at {', '.join(ENTITY_PATHS)} and no ProfilePage JSON-LD; the page that answers 'who is {name or 'this person'}' is the top citation lever")
    else:
        lead = entity["text"][:300]
        epath = urllib.parse.urlsplit(entity_url).path
        if name and re.search(rf"{re.escape(name)}\s+is\b", lead):
            ok("C1", f"{epath} opens with '{name} is …' in the first 300 chars")
        elif name:
            no("C1", f"{epath} does not open with '{name} is …' in the first 300 chars; cited text is definitional and front-loaded")
        else:
            no("C1", f"{epath} found; pass --name to check for a definitional first sentence")
    if person is None:
        no("C2", "no Person JSON-LD on the homepage or entity page")
    else:
        missing = [k for k in ("@id", "sameAs", "worksFor", "knowsAbout", "description") if not person.get(k)]
        same = person.get("sameAs") or []
        if not missing and len(same) >= 5:
            ok("C2", f"Person JSON-LD has @id, description, worksFor, knowsAbout, {len(same)} sameAs")
        else:
            no("C2", f"Person JSON-LD missing {', '.join(missing) or 'nothing'}; sameAs={len(same)} (want 5+)")
    if any(n.get("@type") == "__invalid__" for n in home["ld"] + (entity or home)["ld"]):
        no("C3", "a JSON-LD block does not parse")
    else:
        ok("C3", "all JSON-LD blocks parse")

    # --- D. Consistent ---
    ident = (person or {}).get("description", "")
    surfaces = {
        "meta description": home["meta"].get("description", ""),
        "og:description": home["meta"].get("og:description", ""),
    }
    st, _, llms = fetch(origin + "/llms.txt", accept="text/plain,*/*")
    if st == 200:
        m = re.search(r"^>\s*(.+)$", llms, re.M)
        surfaces["llms.txt blockquote"] = m.group(1).strip() if m else ""
    if not ident:
        no("D1", "Person.description is empty; there is no canonical identity line to compare")
    else:
        # A definitional form ("Name is ...") counts as the same line: it is the
        # first-sentence shape citation studies favor.
        defn = re.compile(rf"^{re.escape(name)}\s+is\b") if name else None
        drift = [k for k, v in surfaces.items() if v and ident not in v and v not in ident and not (defn and defn.match(v))]
        if drift:
            no("D1", f"identity line differs on: {', '.join(drift)}; one string, everywhere")
        else:
            ok("D1", f"identity line matches on {', '.join(k for k, v in surfaces.items() if v)}")
    if entity is None:
        no("D2", "no entity page to carry dated facts")
    else:
        years = set(re.findall(r"\b(?:19|20)\d{2}\b", entity["text"]))
        if len(years) >= 3:
            ok("D2", f"entity page carries dated facts ({len(years)} distinct years)")
        else:
            no("D2", f"entity page has {len(years)} distinct years; roles and works need dates")

    # --- E. Fresh ---
    if lastmods and len(set(lastmods)) >= min(3, len(lastmods)):
        ok("E1", f"sitemap lastmod has {len(set(lastmods))} distinct dates")
    elif lastmods:
        no("E1", f"all {len(lastmods)} sitemap lastmod values are '{lastmods[0]}'; a uniform build date is not a freshness signal")
    else:
        no("E1", "sitemap has no lastmod")
    if entity is None:
        no("E2", "no entity page to carry an Updated date")
    else:
        dm = next((n.get("dateModified") for n in entity["ld"] if n.get("dateModified")), None)
        if dm or re.search(r"\bupdated\b[^.]{0,40}\b(?:19|20)\d{2}\b", entity["text"], re.I):
            ok("E2", f"entity page states a modification date ({dm or 'visible Updated line'})")
        else:
            no("E2", "entity page shows no 'Updated' date and no JSON-LD dateModified")

    # --- F. Discoverable ---
    if st != 200:
        no("F1", f"llms.txt returned {st} (cheap to add; coding agents use it when pointed at the site)")
    else:
        h1 = llms.lstrip().startswith("# ")
        bq = bool(re.search(r"^>", llms, re.M))
        h2 = bool(re.search(r"^## ", llms, re.M))
        links_entity = bool(entity_url and entity_url in llms)
        if h1 and bq and h2 and links_entity:
            ok("F1", "llms.txt has H1, blockquote, H2 lists, and links the entity page")
        else:
            no("F1", f"llms.txt shape: H1={h1} blockquote={bq} H2={h2} links entity page={links_entity}")
        own = set(re.findall(rf"\]\(({re.escape(origin)}[^)\s]*)\)", llms))
        own = {x.rstrip("/") for x in own if not re.search(r"\.(txt|xml|md|pdf|zip)$", x)}
        listed = {x.rstrip("/") for x in urls}
        orphan = sorted(own - listed) if urls else []
        if orphan:
            no("F2", f"llms.txt links {len(orphan)} pages missing from sitemap: {', '.join(urllib.parse.urlsplit(o).path for o in orphan[:6])}")
        elif urls:
            ok("F2", "every page llms.txt links is in the sitemap")
    stm, hdm, bm = fetch(origin + "/", accept="text/markdown")
    alt_md = any(l.get("rel") == "alternate" and "markdown" in (l.get("type") or "") for l in home["links"])
    if "text/markdown" in hdm.get("Content-Type", "") or alt_md:
        info("F3", "markdown available (Accept negotiation or rel=alternate); coding agents fetch it directly")
    else:
        info("F3", "no markdown variant (optional; HTML that passes B2 is enough)")

    # --- G. Recoverable ---
    st, hd, b = fetch(origin + "/__agent_visible_probe__", accept="*/*")
    same_origin_links = len(re.findall(rf"(?:{re.escape(origin)}|\]\(/|href=\"/)", b))
    if st in (404, 410) and same_origin_links >= 2:
        ok("G1", f"404 body for curl-like clients links {same_origin_links} entry points")
    else:
        no("G1", f"404 for Accept */* is {st} with {same_origin_links} same-origin links; a dead link should hand the agent a way back")
    st, _, b = fetch(origin + "/__agent_visible_probe__", accept="text/html")
    t404 = parse_html(b)["text"]
    says_404 = bool(re.search(r"not found|doesn.t exist|does not exist|no such page|\b404\b", t404, re.I))
    # Sites that reuse a masthead H1 on every page still pass: what matters is
    # that the no-JS text says "not found" instead of being the homepage body.
    if st in (404, 410) and says_404 and t404[:MIN_TEXT] != home["text"][:MIN_TEXT]:
        ok("G2", "404 HTML says so without JavaScript")
    elif st in (404, 410):
        no("G2", "404 HTML's no-JS content is the homepage (or never says 'not found'); text-only agents read the wrong page and browsers flash it before the client router runs")
    else:
        no("G2", f"404 HTML is {st}")

    return out, name


MANUAL = """
H. Off-site (manual)
  H1  The same identity line is in the GitHub bio, LinkedIn headline, X bio, and blog/Medium bio.
  H2  Each of those profiles links back to the site; the site's Person.sameAs lists each of them.
  H3  Every paper, talk, and repo names the person as author with the same name spelling.
  H4  Employer pages (team page, LinkedIn company) name the person and role.
  H5  Content is first-hand and dated; refreshed pages beat new ones for citation.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("origin", help="https://example.com (the canonical host)")
    ap.add_argument("--name", help="person's name if not derivable from JSON-LD or H1")
    ap.add_argument("--pages", type=int, default=30, help="max sitemap pages to fetch")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()
    results, name = run(a.origin, a.name, a.pages)
    if a.json:
        print(json.dumps({"name": name, "results": [dict(zip(("status", "check", "detail"), r)) for r in results]}, indent=2))
        return
    print(f"site-for-agents — {a.origin} — entity: {name or '?'}\n")
    for status, code, msg in results:
        print(f"  {status:4} {code}  {msg}")
    passed = sum(1 for s, _, _ in results if s == "PASS")
    failed = sum(1 for s, _, _ in results if s == "FAIL")
    print(f"\n  {passed} pass, {failed} fail, {len(results) - passed - failed} info")
    print(MANUAL)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
