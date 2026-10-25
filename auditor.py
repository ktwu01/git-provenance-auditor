#!/usr/bin/env python3
"""
Git Provenance Auditor
Scan a Git repository's history for evidence of AI involvement,
and produce an Evidence Ledger that separates what Git supports
from what it does not support.

No dependencies. Requires git on PATH.
Usage:
  python3 auditor.py /path/to/repo [--out ledger.md] [--json ledger.json]
  python3 auditor.py https://github.com/owner/repo  (clones to temp dir)
"""
import argparse, json, re, subprocess, sys, tempfile, os
from collections import Counter, defaultdict
from datetime import datetime, timezone

AI_PATTERNS = {
    "Claude / Anthropic": re.compile(r"claude|anthropic", re.I),
    "GPT / OpenAI": re.compile(r"\bgpt\b|openai|codex|chatgpt", re.I),
    "Gemini / Google": re.compile(r"gemini|bard|google ai", re.I),
    "Copilot": re.compile(r"copilot", re.I),
    "Cursor / other agents": re.compile(r"cursor|aider|windsurf|continue\.dev|cody", re.I),
}
AGENT_RULE_FILES = [
    "AGENTS.md","CLAUDE.md",".claude/",".cursorrules",".cursor/",".github/copilot-instructions.md",
    ".aider","GEMINI.md",".windsurf/",
]
TRACE_HINTS = re.compile(r"scratchpad|trace|transcript|prompt|agent[-_ ]log|session.*\.md$", re.I)

def git(repo, *args):
    return subprocess.check_output(["git","-C",repo,*args], text=True, errors="replace")

def scan(repo):
    log = git(repo, "log", "--all", "--pretty=format:%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b%x1e")
    commits=[]
    trailer_hits=Counter(); body_hits=Counter(); coauthors=Counter()
    for rec in log.split("\x1e"):
        rec=rec.strip("\n")
        if not rec.strip(): continue
        parts=rec.split("\x1f")
        if len(parts)<6: continue
        h,an,ae,date,subj,body=parts[:6]
        commits.append({"hash":h,"author":an,"email":ae,"date":date,"subject":subj})
        text=subj+"\n"+body
        for m in re.finditer(r"Co-Authored-By:\s*(.+)", body, re.I):
            coauthors[m.group(1).strip()] += 1
            for label,pat in AI_PATTERNS.items():
                if pat.search(m.group(1)): trailer_hits[label]+=1
        for label,pat in AI_PATTERNS.items():
            if pat.search(text): body_hits[label]+=1
    try:
        files = git(repo, "log", "--all", "--pretty=format:", "--name-only").splitlines()
    except subprocess.CalledProcessError:
        files=[]
    files=[f.strip() for f in files if f.strip()]
    file_counter=Counter(files)
    rule_files=sorted({f for f in file_counter if any(f==r or f.startswith(r) for r in AGENT_RULE_FILES)})
    trace_files=sorted({f for f in file_counter if TRACE_HINTS.search(f)})[:50]
    return {
        "repo": os.path.abspath(repo),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "total_commits": len(commits),
        "date_range": [commits[-1]["date"], commits[0]["date"]] if commits else [],
        "authors": Counter(c["author"] for c in commits),
        "co_authored_by_trailers": dict(coauthors),
        "ai_trailer_hits_by_family": dict(trailer_hits),
        "ai_mentions_in_messages_by_family": dict(body_hits),
        "agent_rule_files_seen_in_history": rule_files,
        "possible_trace_or_scratchpad_files": trace_files,
        "most_touched_files": file_counter.most_common(10),
        "commits_sample_first_5": commits[:5],
    }

def ledger_md(d):
    lines=[]
    lines.append("# PROVENANCE EVIDENCE LEDGER\n")
    lines.append(f"Repository: `{d['repo']}`  ")
    lines.append(f"Scanned: {d['scanned_at']}  ")
    if d["date_range"]: lines.append(f"Commit range: {d['date_range'][0]} to {d['date_range'][1]}  ")
    lines.append(f"Total commits scanned: **{d['total_commits']}**\n")
    lines.append("## Evidence found\n")
    lines.append(f"- Co-Authored-By trailers: {d['co_authored_by_trailers'] or 'none'}")
    lines.append(f"- AI trailer hits by family: {d['ai_trailer_hits_by_family'] or 'none'}")
    lines.append(f"- AI mentions in commit messages by family: {d['ai_mentions_in_messages_by_family'] or 'none'}")
    lines.append(f"- Agent rule files seen in history: {d['agent_rule_files_seen_in_history'] or 'none'}")
    lines.append(f"- Possible trace / scratchpad files: {d['possible_trace_or_scratchpad_files'] or 'none'}\n")
    lines.append("## Supported by this evidence\n")
    lines.append("✓ A listed file was modified in the history scanned")
    lines.append("✓ A listed trace / rule file existed at some revision")
    lines.append("✓ A trailer or message explicitly naming a model family was present on the commits counted above\n")
    lines.append("## NOT supported by this evidence\n")
    lines.append("✗ A percentage of 'AI involvement' in the project")
    lines.append("✗ 'AI authored N commits' (a trailer is not authorship, and absence is not non-involvement)")
    lines.append("✗ Absence of a trailer = absence of AI assistance")
    lines.append("✗ Which parts of a diff were written by a human vs. a model\n")
    lines.append("> That gap, between what Git records and what actually happened, is the finding. Do not upgrade counts above into authorship claims.")
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", default="PROVENANCE_LEDGER.md")
    ap.add_argument("--json", default="provenance_ledger.json")
    a=ap.parse_args()
    repo=a.repo; tmp=None
    if repo.startswith("http"):
        tmp=tempfile.mkdtemp(prefix="gpa-")
        subprocess.check_call(["git","clone","--quiet",repo,tmp+"/repo"])
        repo=tmp+"/repo"
    d=scan(repo)
    d["authors"]=dict(d["authors"])
    open(a.out,"w").write(ledger_md(d))
    open(a.json,"w").write(json.dumps(d, indent=2))
    print(f"Scanned {d['total_commits']} commits. Wrote {a.out} and {a.json}")

if __name__=="__main__": main()
