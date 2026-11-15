# Dev calibration run provenance

- Collection source commit: `6fe6a0e`
- Frozen protocol SHA-256 at collection time:
  `6b0a39251c0e584ff85251d1500ad7e14b3a3758d276d835bca17b58c0960beb`
- Requests expected / received / accounted: `80 / 80 / 80`
- In-flight markers remaining: `0`
- Model metadata unchanged across the run: `true`
- Generation options identical for all requests: `true`

The only later change to `config/protocol.json` adds analysis-only paths and a
language-identification threshold (`latin_exemptions_path`,
`language_id_model_path`, and `language_id_threshold`). Model definitions and
generation controls are byte-for-byte unchanged from the collection source
commit. `scripts/normalize_run_manifest.py` replaced machine-local absolute
paths with repository-relative paths after collection; it did not alter any
request or response receipt.
