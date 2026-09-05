# Levers, ranked, with evidence

Collected 2026-09-04 for a personal site. Dates are the source's own. Vendor
blogs are marked (vendor); prefer log studies, papers, and platform docs.

## 1. A definitional, front-loaded entity page

44.2% of ChatGPT citations come from the first 30% of a page. Cited passages
are ~2× more likely to use "X is …" definitions and average 20.6% proper nouns
(Indig, 1.2M answers, Feb 2026).
https://searchengineland.com/chatgpt-citations-content-study-469483

## 2. The page answers the question it is asked

62.2% of diagnosed citation failures are semantic misalignment: the page
answers a different question. Put the literal question as an H2/H3 and answer
it directly (AgentGEO, arXiv Mar 2026). https://arxiv.org/abs/2603.09296

## 3. Server-rendered content

None of GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot,
PerplexityBot, Meta-ExternalAgent execute JavaScript; only Gemini via Googlebot
does. https://vercel.com/blog/the-rise-of-the-ai-crawler (Dec 2024, vendor);
https://www.asklantern.com/blogs/ai-crawlers-do-not-render-javascript (Jun 2026)

## 4. Allow the answer bots

robots.txt is fetched constantly (OpenAI 3,990× vs 7× for llms.txt across 83
sites in 12 weeks). Opted-out sites "will not be shown in ChatGPT search
answers"; Claude-SearchBot/Claude-User opt-out "may reduce visibility".
https://developers.openai.com/api/docs/bots ;
https://support.claude.com/en/articles/8896518 ;
https://www.ezy.ai/research/do-ai-bots-read-llms-txt (Jul 2026)

## 5. One bio, everywhere, with a sameAs graph

Entity SEO for people: stable ID, identical fact formulation, 15–25
bidirectional profiles, topic co-occurrence, independent verification.
https://www.muratulusoy.de/en/blog/entity-seo-for-people.html (Apr 2026);
https://ipullrank.com/ai-search-entity-recognition

## 6. First-hand, multi-angle content on the target topics

Google: unique first-hand content "will likely influence your presence in
generative AI search more than any other suggestion". Top 30 domains per topic
take 67% of ChatGPT citations; 32.9% of cited pages surfaced only through
fan-out queries.
https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
(updated 2026-07-10);
https://www.airops.com/report/influence-of-retrieval-fanout-and-google-serps-in-chatgpt (Mar 2026, vendor)

## 7. Honest freshness

75% of pages cited by ChatGPT/Gemini/Perplexity were updated in the last
year; refreshed old pages beat new ones (Seer, 7,683 pages, Jul 2026). A recent
timestamp is one of four factors with odds ratio >100 in a 252k-trial
controlled study (Sprinklr, SIGIR 2026).
https://www.seerinteractive.com/insights/study-content-recencys-impact-on-ai-visibility-in-2026 ;
https://arxiv.org/abs/2605.25517

## 8. Long-form on LinkedIn and authored READMEs

LinkedIn is the #2 most-cited domain in AI search (11% of answers); individual
creators are cited 59% of the time; 500–2,000-word originals correlate with
citation, reshares almost never.
https://www.semrush.com/blog/linkedin-ai-visibility-study/ (Mar 2026, vendor)

## 9. Evidence density on challenger pages

Princeton GEO (KDD 2024): citations, quotations, statistics gave +30–40%
visibility; keyword stuffing at or below baseline; "authoritative tone" no
significant gain. Lift is rank-dependent: helps pages retrieved but not cited,
can hurt the page already ranked first. https://arxiv.org/abs/2311.09735

## 10. Person / ProfilePage / Article JSON-LD

Google documents `ProfilePage` for an about page and says structured data is
not required for AI features; Bing confirmed its LLMs use schema. Causal
evidence for schema as a citation lever is weak; ship it for eligibility.
https://developers.google.com/search/docs/appearance/structured-data/profile-page ;
https://searchengineland.com/microsoft-bing-copilot-use-schema-for-its-llms-453455

## 11. llms.txt: keep it, expect little

Spec v2 (Aug 2026) adds `rel="alternate"`/`describedby` discovery, `page.md`
or `page.html.md`, subpath scoping, and lists "a personal site answering
questions about someone's CV" as a use case. Server logs: OpenAI 7 fetches,
Anthropic 9, Perplexity 0 across 83 sites in 12 weeks. Google Search ignores
it. Coding agents use it when pointed at the site.
https://llmstxt.org ; https://llmstxt.org/changes.html ;
https://www.ezy.ai/research/do-ai-bots-read-llms-txt ;
https://dejan.ai/blog/crawler-census-robots-llms-okf/ ;
https://developer.chrome.com/docs/lighthouse/agentic-browsing/llms-txt

## 12. Markdown negotiation

Claude Code, Cursor, OpenCode send `Accept: text/markdown`; Codex, Gemini CLI,
Copilot, Windsurf do not (Feb 2026). Cloudflare and Vercel document edge
support. Optional; HTML that reads without JS is the requirement.
https://www.checklyhq.com/blog/state-of-ai-agent-content-negotation/ ;
https://blog.cloudflare.com/markdown-for-agents/ ;
https://vercel.com/blog/making-agent-friendly-pages-with-content-negotiation

## 13. Usage-rights signals

`Content-Signal: search=yes, ai-input=yes, ai-train=yes` in robots.txt
(Cloudflare, Sep 2025). IETF aipref drafts define `Content-Usage:`; not yet an
RFC. Zero visibility upside; one line.
https://blog.cloudflare.com/content-signals-policy/ ;
https://datatracker.ietf.org/doc/draft-ietf-aipref-vocab/

## 14. Wikidata only after independent references

Needs "serious and publicly available references"; LinkedIn, self-published
pages, Crunchbase do not count; disclose COI.
https://www.wikidata.org/wiki/Wikidata:Notability

## 15. Skip service-discovery files for a person

`.well-known/agent-card.json` (A2A), `/.well-known/mcp-server`, `ai.txt`
describe services, not people. No answer engine reads them for entity facts.
