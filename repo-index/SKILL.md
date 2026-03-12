---
name: repo-index
description: Discovers all git repositories under a given root folder and writes a JSON reference file recording each repo's name, path, remote URL, and primary tech stack. Use this skill whenever the user wants to catalog, map, or index their local repositories, populate a repos.json reference file, or create a machine-readable list of where their projects live on disk. Also invoke this skill proactively when another skill needs to locate repos and no reference file exists yet.
---

# Repo Index

This skill scans a folder for git repositories and writes a structured JSON file cataloging each one. The output is intended to be read by other skills or scripts that need to know where projects live without re-scanning the filesystem every time.

The scripts for this skill live at `scripts/` relative to this skill file. Resolve their absolute paths before invoking them — e.g. if this skill file is at `/path/to/repo-index/SKILL.md`, the scripts are at `/path/to/repo-index/scripts/`.

## Step 1: Gather inputs

**Search root** — check the environment variable `$AGENTS_REPOS_ROOT` first:
- If set, use it as the search root without asking.
- If not set, stop and tell the user:
  > `AGENTS_REPOS_ROOT` is not set. Please add `export AGENTS_REPOS_ROOT="<path to your repos>"` to your shell config (`~/.bashrc`, `~/.zshrc`, or equivalent), then start a new shell session and try again.

**Output file path** — ask the user if not already provided:
- *"Where should I save the reference file? (e.g. `~/repos.json`)"*

Expand `~` to the user's home directory in both paths before proceeding.

If the output file already exists, ask: *"That file already exists — should I overwrite it, or merge the new results in (keeping existing entries and updating any that have changed)?"*

## Step 2: Discover repositories

Use `find-repos.sh`:

```bash
<skill_dir>/scripts/find-repos.sh "<root>"
```

Each line of output is a repo root path. Display the list, then ask:

*"Should any of these repositories be excluded? If so, enter their names or numbers (comma-separated), or press enter to continue."*

Remove excluded repos from the list before proceeding. All subsequent steps only operate on the remaining repos.

## Step 3: Collect metadata

Pipe the repo list into `collect-metadata.py` once:

```bash
<skill_dir>/scripts/collect-metadata.py --root "<root>" < <(find-repos output)
```

Output is tab-separated with four fields per line: `<path>\t<name>\t<remote_url>\t<stack>`. Remote URL is empty string if no `origin` remote exists; stack is `unknown` if nothing is detected.

The script detects the following stacks (multiple may apply to one repo):

| Indicator | Stack |
|---|---|
| `angular.json` | Angular |
| `package.json` | Node.js |
| `pom.xml` (root or one level deep) | Java (Maven) |
| `go.mod` | Go |
| `requirements.txt`, `pyproject.toml`, or `setup.py` | Python |
| `*.tf` (up to 3 levels, skips `.terraform/`) | Terraform |
| `Dockerfile` (up to 3 levels) | Docker |
| `kustomization.yaml/yml` (up to 4 levels) | Kustomize |
| `Chart.yaml` (up to 4 levels) | Helm |
| `Cargo.toml` | Rust |
| `Gemfile` | Ruby |
| `mix.exs` | Elixir |

## Step 4: Write the output file

**If overwriting:** write the file fresh.

**If merging:** read the existing file, then upsert by `path` — add new repos and update metadata for repos whose path already exists.

Sort the final `repos` array alphabetically by `name` before writing.

Use the TSV output from `collect-metadata.py` directly for each repo's `path`, `name`, `remote_url`, and `stack` fields — do not re-expand or reformat the paths. The script outputs `$AGENTS_REPOS_ROOT/...` paths when `--root` is passed; carry them through verbatim.

Set `search_root` to the literal string `"$AGENTS_REPOS_ROOT"` (not the expanded path).

Output format:

```json
{
  "search_root": "$AGENTS_REPOS_ROOT",
  "repos": [
    {
      "name": "my-service",
      "path": "$AGENTS_REPOS_ROOT/my-service",
      "remote_url": "git@github.com:org/my-service.git",
      "stack": "Go"
    },
    {
      "name": "infra",
      "path": "$AGENTS_REPOS_ROOT/infra",
      "remote_url": "git@github.com:org/infra.git",
      "stack": "Terraform"
    }
  ]
}
```

## Step 5: Confirm

Tell the user:
- How many repos were written to the file and where it was saved
- A brief table of name, path, and stack so they can spot-check the results
