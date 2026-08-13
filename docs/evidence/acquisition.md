# Evidence acquisition

The v0.9.3 gateway has fixed adapters for PubMed/NCBI, Crossref and optional OpenAlex. User-controlled hosts are not accepted. The existing outbound HTTP guard enforces HTTPS, host/DNS/private-IP policy, redirect revalidation, timeout and response-size limits.

PubMed sends `tool` and configured contact email, batches IDs, reads JSON search/summary data and performs a bounded structured XML fetch. DTDs and entities are rejected. Crossref sends polite `mailto` and User-Agent identification and retries 429/5xx once with bounded backoff. OpenAlex requires `OPENALEX_API_KEY`; without it, that provider degrades without breaking the workspace. Credentials are never persisted in plans, identifiers or audit details.

Search plans are versioned and content-hashed. Acquisition runs retain provider status and provenance. Dedupe prefers DOI, PMID/PMCID and OpenAlex ID; title/year ambiguity remains `needs_review` rather than being irreversibly merged.

Retrieved records are metadata-only unless rights are independently verified. Metadata access does not imply permission to retain or redistribute full text. No paywall bypass, publisher scraping or general crawler exists.
