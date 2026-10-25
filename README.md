# Git Provenance Auditor

What can a Git repository actually tell you about AI involvement in research?

AI coding agents are already participating in scientific research. The two repositories audited in the paper used Claude Code and Cursor. This tool audits a repository's history and produces a **Provenance Evidence Ledger**: what Git supports, and, just as important, what it does not support.

## Run it

```bash
python3 auditor.py /path/to/repo
# or
python3 auditor.py https://github.com/owner/repo
```

Outputs `PROVENANCE_LEDGER.md` and `provenance_ledger.json`. No dependencies, only Git and Python 3.

## What it scans

- `Co-Authored-By:` trailers, grouped by model family (Claude, GPT, Gemini, Copilot, Cursor and others)
- AI mentions in commit messages
- Agent rule files in history (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`, Copilot instructions, etc.)
- Possible trace / scratchpad files
- Commit count, date range, authors, most-touched files

## What the ledger will not claim

- A percentage of "AI involvement"
- That AI authored N commits
- That no trailer means no AI was used

That restraint is the point. In the study behind this tool, 569 commits from AI-assisted scientific research were audited, and the most obvious quantitative signals often gave confident but incorrect answers.

## Background

Companion artifact for:

**What Git Does Not Record: Provenance Legibility in Two AI-Assisted Research Repositories**
Koutian Wu, Zesen Huang, Hejia Geng. NeurIPS 2026 AI-Native Academia Workshop.
arXiv:2610.28655 (submitted 9 Oct 2026) — https://arxiv.org/abs/2610.28655

The paper audits two single-investigator repositories of 466 and 103 commits (569 total), each with a different class of agent residue: a prescriptive trace of standing rule files, and a narrative trace of a running agent scratchpad. An auditable evidence ledger is included as ancillary files on arXiv.
