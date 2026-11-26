# Sources

Every outside fact the project relies on: one YAML list per topic. Each entry has `key`, `title`, `publisher`, `url`,
`date_accessed`, and `quotes` (exact text, a locator, and the claim it supports). Cite one in any file as
`[src:key]`; `make check` fails on a citation with no entry, or an entry with no URL, quote or date.
