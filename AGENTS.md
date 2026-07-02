# AGENTS.md

## Cursor Cloud specific instructions

### Repository shape (important)
The default branch (`claude/initial-setup-ndzE7`) has an **empty working tree** — the project
files live only in the open PR branch (`claude/hello-claude-page-b27ZT`). When that PR is merged
the following files appear at the repo root:

- `index.html` — Product A: a self-contained static "Hello, Claude Code!" welcome page (inline
  CSS, glassmorphism card, animations). No JS, no build, no dependencies.
- `mohrss_annuity_downloader.py` — Product B: a standalone Python 3.10+ CLI that scrapes the
  Chinese MOHRSS site for enterprise-annuity articles and downloads their attachments.
- `requirements.txt` — pip dependencies for Product B (`requests`, `beautifulsoup4`, `schedule`).

There are **no databases, Redis, containers, or long-running backend services**, and **no
lint/test/build pipelines**. `python3` (3.12) is preinstalled.

### Dependencies
Python packages are installed from `requirements.txt`. Because this environment uses the system
Python, install with `pip3 install --break-system-packages -r requirements.txt` (this is what the
startup update script does, guarded so it is a no-op when `requirements.txt` is absent).

### Running Product A (static welcome page)
Serve from the repo root and open `index.html`:

```bash
python3 -m http.server 8000   # then visit http://localhost:8000/index.html
```

### Running Product B (annuity downloader) — gotchas
- Invoking `python3 mohrss_annuity_downloader.py` runs one pass immediately, then **blocks forever**
  in a `schedule` loop (re-runs every 24h). Do **not** run it that way when you just want to verify.
- To test a single non-blocking pass, call the task function directly:

  ```bash
  python3 -c "import mohrss_annuity_downloader as m; m.run_download_task()"
  ```

- It fetches `https://www.mohrss.gov.cn` over the network. If egress is restricted or the site's
  page structure differs, it logs "共找到 0 篇目标文章" (0 articles found) and exits cleanly rather
  than erroring — a 0-article run still proves the environment works.
- Outputs are written to `mohrss_annuity_data/` (with a `.downloaded_urls.txt` dedup state file)
  and to `downloader.log`.
