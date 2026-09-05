# WebMCP tools for a personal site

Working example, adapted from a live site (2026-09). Facts come from the
site's single fact source; tools serialize it. Register on every page that
has the facts; on static pages without the app bundle, bundle this module
(esbuild `--bundle --format=iife --minify`) and inline it.

```ts
import { PROFILE, SITE_URL } from "./profile";

const READ_ONLY = { readOnlyHint: true, consequentialHint: false, untrustedContentHint: false };
const json = (v: unknown) => JSON.stringify(v, null, 2);

export const TOOLS = [
  {
    name: "get_profile",
    description: `Get ${PROFILE.name}'s profile: identity line, current role, location, languages, primary links.`,
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    annotations: READ_ONLY,
    execute: async () => json({ name: PROFILE.name, identity: PROFILE.identity, location: PROFILE.location, links: PROFILE.links }),
  },
  {
    name: "list_projects",
    description: `List software built by ${PROFILE.name}. Optionally filter by group or keyword.`,
    inputSchema: {
      type: "object",
      properties: {
        group: { type: "string", enum: ["agents", "apps", "tools"], description: "Only this group." },
        query: { type: "string", description: "Case-insensitive keyword on name and description." },
      },
      additionalProperties: false,
    },
    annotations: READ_ONLY,
    execute: async ({ group, query }: { group?: string; query?: string }) =>
      json(PROFILE.projects.filter((p) => (!group || p.group === group) && (!query || `${p.name} ${p.description}`.toLowerCase().includes(query.toLowerCase())))),
  },
  {
    name: "get_experience",
    description: `Get ${PROFILE.name}'s career timeline with dates, education, and papers.`,
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    annotations: READ_ONLY,
    execute: async () => json({ roles: PROFILE.roles, education: PROFILE.education, papers: PROFILE.papers }),
  },
  {
    name: "get_contact",
    description: `How to contact ${PROFILE.name}: email, direct-message channel, public profiles.`,
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    annotations: READ_ONLY,
    execute: async () => json({ email: PROFILE.email, directMessages: PROFILE.links.telegram, profiles: PROFILE.links }),
  },
];

/** Action tool: only if the site already offers the action to humans. */
export const BOOK_CALL = {
  name: "book_call",
  description: `Open ${PROFILE.name}'s booking page for a 30-minute call.`,
  inputSchema: { type: "object", properties: {}, additionalProperties: false },
  annotations: { readOnlyHint: false, consequentialHint: true, untrustedContentHint: false },
  execute: async () => {
    window.open(PROFILE.links.booking, "_blank", "noopener");
    return `Opened ${PROFILE.links.booking}`;
  },
};

export async function register(): Promise<void> {
  const ctx = (document as any).modelContext;
  if (!ctx?.registerTool) return;           // browsers without WebMCP: no-op
  for (const t of TOOLS) await ctx.registerTool(t);
}
```

Rules

- `additionalProperties: false` on every schema; agents fill what the schema
  allows, nothing else.
- `readOnlyHint: true` on Answer tools. `consequentialHint: true` on anything
  that commits the user (booking, payment, subscription); Chrome then
  requires confirmation.
- Descriptions name the person: an agent choosing between tools on several
  open tabs needs to know whose profile this is.
- Test without Chrome: shim `document.modelContext = { registerTool(t) {...} }`,
  load the page headless, call each `execute`, assert the JSON.
- Directory listing: https://webmcp.com → "Scan my site" → "Request
  listing" (needs an email). Rescan after adding tools.
