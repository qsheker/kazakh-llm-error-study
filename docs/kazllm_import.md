# Importing the Official KazLLM GGUF

The study uses the official ISSAI gated artifact, not a community conversion:

- repository: `issai/LLama-3.1-KazLLM-1.0-8B-GGUF4`
- pinned revision: `eb04ab55b920c64dc50583f20de783e1d3034529`
- file: `checkpoints_llama8b_031224_18900-Q4_K_M.gguf`
- local Ollama tag: `kazllm:8b-q4_k_m`

## One-time access step

1. Sign in to Hugging Face in a browser.
2. Open the official repository and accept its access conditions.
3. Authenticate locally with `.venv/bin/hf auth login` and approve the browser
   device flow. Do not paste credentials or tokens into Git, chat logs, shell
   history, screenshots, or the manuscript.

The repository is gated, so the download cannot be completed honestly without the account holder accepting the conditions.

## Reproducible import

After installing project dependencies:

```bash
.venv/bin/hf auth whoami
.venv/bin/python scripts/install_kazllm.py
```

The script downloads only the named file from the pinned repository revision,
computes SHA-256, checks an already frozen hash when present, freezes the first
authenticated official digest when absent, calls `ollama create`, and writes an
import receipt. Commit the digest, manifest, and receipt—not the 4.9 GB GGUF.

The import method follows Ollama's official single-file GGUF procedure: a Modelfile containing `FROM /path/to/file.gguf`, followed by `ollama create`.
