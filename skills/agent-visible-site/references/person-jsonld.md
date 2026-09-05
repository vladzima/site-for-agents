# Person JSON-LD that passes validator.schema.org

Shape used on a live personal site (2026-09). Every page carries the first
four nodes; the entity page adds the rest. `@id` is stable so external pages
can be reconciled against it.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Person",
      "@id": "https://example.com/#person",
      "name": "Full Name",
      "alternateName": "handle",
      "url": "https://example.com/",
      "mainEntityOfPage": "https://example.com/about",
      "description": "Full Name — role. N years; ex-A, B; current role at C.",
      "jobTitle": "Current Title",
      "email": "public@example.com",
      "worksFor": { "@id": "https://employer.com/#organization" },
      "address": { "@type": "PostalAddress", "addressLocality": "City", "addressRegion": "Region", "addressCountry": "US" },
      "alumniOf": [
        { "@type": "EducationalOrganization", "name": "University" },
        { "@type": "Role", "roleName": "Previous Title", "startDate": "2019-03", "endDate": "2021-09",
          "alumniOf": { "@type": "Organization", "name": "Previous Employer", "url": "https://prev.example" } }
      ],
      "hasOccupation": { "@type": "Occupation", "name": "Current Title" },
      "knowsAbout": ["Topic A", "Topic B"],
      "knowsLanguage": ["en"],
      "sameAs": ["https://github.com/handle", "https://www.linkedin.com/in/handle", "https://x.com/handle", "https://blog.example.com"]
    },
    { "@type": "Organization", "@id": "https://employer.com/#organization", "name": "Employer", "url": "https://employer.com",
      "sameAs": ["https://x.com/employer"] },
    { "@type": "Organization", "@id": "https://example.com/#org", "name": "example.com", "url": "https://example.com/",
      "founder": { "@id": "https://example.com/#person" },
      "contactPoint": { "@type": "ContactPoint", "email": "public@example.com", "contactType": "customer support" } },
    { "@type": "WebSite", "@id": "https://example.com/#website", "url": "https://example.com/", "name": "Full Name",
      "publisher": { "@id": "https://example.com/#person" } },

    { "@type": "ProfilePage", "@id": "https://example.com/about", "url": "https://example.com/about",
      "dateModified": "2026-09-04", "mainEntity": { "@id": "https://example.com/#person" },
      "isPartOf": { "@id": "https://example.com/#website" } },
    { "@type": "ScholarlyArticle", "headline": "Paper title", "url": "https://…", "datePublished": "2026",
      "author": { "@id": "https://example.com/#person" } },
    { "@type": "SoftwareSourceCode", "name": "Project", "url": "https://github.com/handle/project",
      "codeRepository": "https://github.com/handle/project", "description": "One line",
      "author": { "@id": "https://example.com/#person" } }
  ]
}
```

Notes

- `OrganizationRole.memberOf` is rejected by the validator; past roles go
  under `alumniOf` as `Role` with dates. `hasOccupation` takes an `Occupation`.
- Generate the block from the fact source and inject it at build; a
  hand-edited `<script type="application/ld+json">` in the template drifts.
- Escape `<` as `\u003c` in the serialized JSON.
- Validate programmatically: POST `html=<page>` to
  `https://validator.schema.org/validate`, strip the `)]}'` prefix, parse.
