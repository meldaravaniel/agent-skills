#!/usr/bin/env python3
"""
Reads repo paths from stdin (one per line) or as arguments.
Outputs one TSV line per repo: <path>\t<name>\t<remote_url>\t<stack>
remote_url is empty string if no origin remote exists.

Usage:
  collect-metadata.py [--root /path/to/root] [repo_path ...]
  find-repos.sh /path/to/root | collect-metadata.py --root /path/to/root

The --root argument sets the prefix to replace with $AGENTS_REPOS_ROOT in output
paths. Falls back to the AGENTS_REPOS_ROOT environment variable if not provided.
"""

import argparse
import configparser
import fnmatch
import os
import sys


ALWAYS_PRUNE = {'.git', '.terraform', 'node_modules', '__pycache__'}


def has_file(root, filename, max_depth, prune=None):
    """Return True if filename exists anywhere under root up to max_depth levels deep.
    Equivalent to: find root -maxdepth max_depth -name filename
    """
    prune = ALWAYS_PRUNE | (prune or set())
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == '.' else rel.count(os.sep) + 1
        if filename in filenames:
            return True
        if depth >= max_depth:
            dirnames.clear()
        else:
            dirnames[:] = [d for d in dirnames if d not in prune]
    return False


def has_glob(root, pattern, max_depth, prune=None):
    """Return True if any file matching glob pattern exists under root up to max_depth."""
    prune = ALWAYS_PRUNE | (prune or set())
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == '.' else rel.count(os.sep) + 1
        if any(fnmatch.fnmatch(f, pattern) for f in filenames):
            return True
        if depth >= max_depth:
            dirnames.clear()
        else:
            dirnames[:] = [d for d in dirnames if d not in prune]
    return False


def detect_stack(path):
    stacks = []
    exists = os.path.exists
    join = os.path.join

    # Angular / Node.js (check angular.json first — it implies Node.js)
    if exists(join(path, 'angular.json')):
        stacks.append('Angular')
    elif exists(join(path, 'package.json')):
        stacks.append('Node.js')

    # Java (Maven) — root or up to 2 levels deep for multi-module projects
    if has_file(path, 'pom.xml', max_depth=2):
        stacks.append('Java (Maven)')

    # Go
    if exists(join(path, 'go.mod')):
        stacks.append('Go')

    # Python — root or up to 2 levels deep
    if (has_file(path, 'requirements.txt', max_depth=2) or
            has_file(path, 'pyproject.toml', max_depth=2) or
            has_file(path, 'setup.py', max_depth=2)):
        stacks.append('Python')

    # Terraform — up to 3 levels deep, skipping .terraform cache
    if has_glob(path, '*.tf', max_depth=3):
        stacks.append('Terraform')

    # Docker — up to 3 levels deep
    if has_file(path, 'Dockerfile', max_depth=3):
        stacks.append('Docker')

    # Kustomize — up to 4 levels deep
    if (has_file(path, 'kustomization.yaml', max_depth=4) or
            has_file(path, 'kustomization.yml', max_depth=4)):
        stacks.append('Kustomize')

    # Helm — up to 4 levels deep
    if has_file(path, 'Chart.yaml', max_depth=4):
        stacks.append('Helm')

    # Root-only single-file checks
    if exists(join(path, 'Cargo.toml')): stacks.append('Rust')
    if exists(join(path, 'Gemfile')):    stacks.append('Ruby')
    if exists(join(path, 'mix.exs')):   stacks.append('Elixir')

    return ','.join(stacks) if stacks else 'unknown'


def get_remote_url(path):
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(path, '.git', 'config'))
    return cfg.get('remote "origin"', 'url', fallback='')


def format_path(path, root=None):
    """Replace the AGENTS_REPOS_ROOT prefix with the variable name.

    Uses the provided root if given, otherwise falls back to the
    AGENTS_REPOS_ROOT environment variable.
    """
    if root is None:
        root = os.environ.get('AGENTS_REPOS_ROOT', '')
    root = root.rstrip(os.sep)
    if root and path.startswith(root + os.sep):
        return '$AGENTS_REPOS_ROOT' + path[len(root):]
    return path


def main():
    parser = argparse.ArgumentParser(description='Collect repo metadata')
    parser.add_argument('--root', default=None,
                        help='Root prefix to replace with $AGENTS_REPOS_ROOT in output paths')
    parser.add_argument('paths', nargs='*',
                        help='Repo paths to process (reads stdin if omitted)')
    args = parser.parse_args()

    paths = args.paths if args.paths else [
        line.rstrip('\n') for line in sys.stdin if line.strip()
    ]
    for path in paths:
        name = os.path.basename(path)
        remote = get_remote_url(path)
        stack = detect_stack(path)
        print(f'{format_path(path, args.root)}\t{name}\t{remote}\t{stack}')


if __name__ == '__main__':
    main()
