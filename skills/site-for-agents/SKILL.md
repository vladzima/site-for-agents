---
name: site-for-agents
description: >
  Use when a personal website, portfolio, CV site, or "about me" page needs to
  be found, read, and quoted correctly by AI agents and answer engines
  (ChatGPT search, Claude, Perplexity, Google AI Mode, coding agents). Also
  use when the user mentions GEO, generative engine optimization, AI SEO,
  llms.txt, "how do I show up in ChatGPT", agent-readiness, or asks why an
  assistant describes them wrongly or not at all.
license: MIT
metadata:
  author: Vlad Arbatov
  version: "0.1.0"
---

# Site for agents

An agent answering "who is X" or "who built Y" needs one fetch that returns
plain text, a definitional first sentence, dated facts, and links that agree
with every other profile of X on the web. Most of what is sold as GEO does
not move citation rate. The things below do, in this order.

Evidence and sources: [references/levers.md](references/levers.md).

## Order of work

1. **Fact source first.** One file holds every fact: identity line, location,
   roles with `YYYY-MM` dates, education, works, links, `updated` date. Every
   surface (meta, JSON-LD, entity page, llms.txt, hero) renders from it. Six
   hand-written copies will disagree within a month; agents read the
   disagreement as unreliability. Never publish phone numbers or private
   emails from an imported CV.
2. **Identity line.** One sentence, plain, proper nouns, no adjectives:
   `Name — role. N years; ex-A, B; current role at C.` Used verbatim in
   `<meta description>`, OG, `Person.description`, `llms.txt` blockquote,
   hero. The definitional form `Name is a … based in …` opens the entity page.
3. **Entity page** (`/about`). Served as HTML with the text already in it;
   answer bots fetch the HTML URL with a browser-like `Accept` and run no JS.
   A markdown twin or `llms.txt` does not substitute: only coding agents send
   `Accept: text/markdown`. Title, description, canonical, and JSON-LD must
   be in the served HTML, not set by client code. Order:
   definition; current work with numbers; dated career timeline; works
   grouped, each "by Name"; writing; education and languages; contact; a
   short Q&A whose H3s are the literal questions agents get asked; visible
   `Updated YYYY-MM-DD`. Cited text comes from the first third of a page.
4. **Structured data.** `Person` with stable `@id`, `alternateName` (handle),
   `worksFor` → `Organization` with `url` and `sameAs`, past roles as
   `alumniOf: Role{roleName,startDate,endDate,alumniOf}`, `knowsAbout`,
   `sameAs` ≥ 5. Entity page adds `ProfilePage{mainEntity,dateModified}` and
   one `ScholarlyArticle` / `SoftwareSourceCode` per work with
   `author → @id`. Validate at validator.schema.org; see
   [references/person-jsonld.md](references/person-jsonld.md).
5. **Freshness.** Per-route `lastmod` from a real date (git log of the
   source), never the build date. `dateModified` and a visible date on the
   entity page.
6. **Discovery files.** `llms.txt` (H1, blockquote = definition, one
   "when to use this" paragraph, `## About / Projects / Writing / Contact /
   Optional`, under ~1,500 tokens, links the entity page). `robots.txt`
   allows `OAI-SearchBot`, `Claude-SearchBot`, `*-User`, `PerplexityBot`;
   optional `Content-Signal:` line. Sitemap lists every route.
7. **Recovery.** Unknown paths return a real 404 whose body, for both
   `Accept: text/html` and `*/*`, says "not found" and links the entry points.
8. **Off-site.** Paste the identity line into GitHub, LinkedIn headline, X,
   blog bio. Tag the employer's handle where the platform links it
   (`@company` on X and GitHub). Each profile links back; `sameAs` lists each.

   Submit the sitemap in Google Search Console and Bing Webmaster Tools;
   Bing feeds ChatGPT search.

Skip unless the site exposes a service: `.well-known` agent cards, MCP
discovery, `ai.txt`. Skip Wikidata until independent references exist.
`Accept: text/markdown` twins are optional; if served, send
`Vary: Accept` so the CDN does not hand one variant to the other client.

## Verify

```bash
python3 scripts/check.py https://example.com --name "Full Name"
```

Groups A–G are automated with a reason per line; H is printed as a manual
list. Then the real test: give a fresh agent only `llms.txt` and the entity
page, ask "who is X and what did X build", and read what it gets wrong.

Run the check against the **canonical host** (the one in `rel=canonical`),
not the alias. Run it after every deploy that touches routing.

## Traps

| Symptom | Cause | Fix |
|---|---|---|
| Browsers get markdown at `/` | A root `index.md` (or any `index.*`) is served by the host before rewrites run | Name the home twin `home.md` |
| 404 flashes the homepage | SPA shell with a homepage no-JS snapshot served as 404 | Build a separate `404.html` whose `#root` is a 404 snapshot |
| Everything passes on `www`, fails on apex | Tested the alias; canonical 308s with a stub body | Flip the primary host; test the canonical |
| Schema validator rejects `hasOccupation` | `OrganizationRole.memberOf` is not a property | Past roles under `alumniOf` as `Role`; current job as `Occupation` |
| Build-output tests fail after a content edit | Tests read a stale `dist/` | `rm -rf dist && build` before the test run |
| Browsers sometimes get markdown, agents HTML | Negotiated responses cached without `Vary: Accept` | Add `Vary: Accept` to both variants |
| "Contact on Telegram" points at a channel | Link labelled by platform, not by purpose | Separate `contact` and `channel` links; label the channel's language |
