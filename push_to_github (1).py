#!/usr/bin/env python3
"""
push_to_github.py - push the current project folder to a NEW GitHub repo.

SETUP (one time, ~2 minutes)
  1. Save this file somewhere handy, e.g.  C:\\Tools\\push_to_github.py
  2. Open it in any editor and paste your token into CONFIG below:
         GITHUB_TOKEN = "ghp_..."
     Get one at:  GitHub -> Settings -> Developer settings ->
     Personal access tokens -> Tokens (classic) -> Generate new token
     and check the [repo] scope. (GITHUB_USER is optional; if you leave it
     empty the script figures it out from the token.)
  3. In VSCode: open your project, open the terminal (Ctrl+`), then run:
         py C:\\Tools\\push_to_github.py
     ('python C:\\Tools\\push_to_github.py' works too. Python 3.8+,
     no pip installs needed, Git must be installed.)

WHAT IT DOES (all from the terminal, with prompts)
  - asks for the repo name      (prefilled with the project folder name)
  - asks private or public      (default: public)
  - asks for final confirmation
  - creates the repo on GitHub
  - git init (if needed) + commits everything (respects .gitignore)
  - pushes to the new repo      (your token is NEVER saved into the project)
  - prints the repo URL

OPTIONS (all optional)
  py push_to_github.py my-repo-name    override the suggested repo name
  --private                            make the repo private
  --yes                                skip all prompts (uses defaults)

TIPS
  - If 'py' is not recognised, run:  py --version   (or install Python
    from python.org, ticking "Add to PATH" during setup).
  - You can also put your token in an env var  GITHUB_TOKEN  instead of
    editing the file, or in a  push_to_github.json  file next to this
    script:   { "token": "ghp_...", "user": "optional" }
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser

# ================================ CONFIG ===================================
GITHUB_USER  = ""                # optional, e.g. "octocat"
GITHUB_TOKEN = "PASTE-YOUR-TOKEN-HERE"
# =============================================================================

API = "https://api.github.com"


# ----------------------------- tiny UI helpers ------------------------------

class C(object):
    """ANSI colours, auto-disabled when not on a real terminal."""
    def __init__(self):
        self.on = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

    def _w(self, code, s):
        return "\033[%sm%s\033[0m" % (code, s) if self.on else s

    def green(self, s):
        return self._w("32", s)

    def red(self, s):
        return self._w("31", s)

    def yellow(self, s):
        return self._w("33", s)

    def bold(self, s):
        return self._w("1", s)


AUTO_YES = False


def ask(prompt, default=""):
    """Ask for a line of input, with an optional default."""
    suffix = " [%s]" % default if default else ""
    try:
        v = input("%s%s: " % (prompt, suffix)).strip()
    except EOFError:
        return default
    return v or default


def yes(prompt, default=True):
    """Yes/no question. [Y/n] when default, [y/N] when not."""
    if AUTO_YES:
        print("%s (yes)" % prompt)
        return True
    tag = "Y/n" if default else "y/N"
    try:
        v = input("%s [%s]: " % (prompt, tag)).strip().lower()
    except EOFError:
        return default
    if not v:
        return default
    return v in ("y", "yes")


def die(color, msg, code=1):
    red = getattr(color, "red", None) or (lambda s: s)
    print(red("Error: ") + msg)
    sys.exit(code)


def step(color, n, total, msg):
    print(color.bold("[%d/%d] ") % (n, total) + msg)


# ----------------------------- credentials ---------------------------------

def is_placeholder(token):
    return (not token) or token.startswith("PASTE-YOUR") or token.startswith("ghp_paste")


def load_credentials():
    """Order: this file's CONFIG -> push_to_github.json -> env vars."""
    user, token = GITHUB_USER, GITHUB_TOKEN

    here = os.path.dirname(os.path.abspath(__file__))
    for path in (os.path.join(here, "push_to_github.json"),
                 os.path.join(os.path.expanduser("~"), ".push_to_github.json")):
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    d = json.load(f)
                if d.get("token"):
                    token = d["token"]
                if d.get("user"):
                    user = d["user"]
                break
            except Exception:
                pass

    env_tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if env_tok:
        token = env_tok

    if is_placeholder(token):
        if not sys.stdin.isatty():
            die(None, "no token found. Set GITHUB_TOKEN in the script CONFIG, "
                      "or a push_to_github.json file next to it, or the "
                      "GITHUB_TOKEN environment variable.")
        print("No token configured yet - let's set one up.")
        print("Create it at: GitHub -> Settings -> Developer settings ->")
        print("Personal access tokens -> Tokens (classic) -> 'repo' scope.\n")
        try:
            token = input("Paste your Personal Access Token (ghp_...): ").strip()
        except EOFError:
            pass
        if not token:
            die(None, "no token given, aborting.")
        if yes("Save it to push_to_github.json next to the script so you don't "
               "have to paste it again? [Y/n]"):
            cfg = {"user": user, "token": token}
            try:
                with open(os.path.join(here, "push_to_github.json"), "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
                print("Saved to %s" % os.path.join(here, "push_to_github.json"))
            except Exception as e:
                print("(could not save: %s)" % e)

    return user, token


# ----------------------------- GitHub API ----------------------------------

def api(method, path, token=None, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "push_to_github.py")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"message": raw[:400]}
    except urllib.error.URLError as e:
        return None, {"message": "network problem: %s" % e.reason}


def api_user(token):
    st, d = api("GET", "/user", token)
    if st != 200 or not isinstance(d, dict):
        msg = (d or {}).get("message", "unknown error") if isinstance(d, dict) else "?"
        if st == 401:
            die(None, "GitHub rejected the token (401). Check that GITHUB_TOKEN "
                      "in the script is correct and not expired.")
        if st == 403:
            die(None, "GitHub refused access (403). The token needs the 'repo' "
                      "scope: Settings -> Developer settings -> Personal access "
                      "tokens -> edit the token -> check [repo].\nDetail: %s" % msg)
        die(None, "could not verify token (HTTP %s): %s" % (st, msg))
    return d  # has: login, name, id


def api_create_repo(token, name, private):
    st, d = api("POST", "/user/repos", token, {
        "name": name,
        "private": bool(private),
        "auto_init": False,
        "description": "Pushed with push_to_github.py",
    })
    if st == 201 and isinstance(d, dict):
        return d
    msg = (d or {}).get("message", "unknown error") if isinstance(d, dict) else "unknown error"
    if st == 422 and "already exists" in msg.lower():
        die(None, "a repository named '%s' already exists on your account - "
                  "pick a different name." % name)
    if st == 404:
        die(None, "no repo named '%s' could be created: %s" % (name, msg))
    die(None, "creating the repo failed (HTTP %s): %s" % (st, msg))


# ------------------------------- git ----------------------------------------

def run(cmd, cwd=None, extra_config=None):
    """Run a command, capture combined output, never raise."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    full = list(cmd)
    if full and full[0] == "git" and extra_config:
        prefix = []
        for k in extra_config:
            prefix += ["-c", k]
        full = ["git"] + prefix + full[1:]
    p = subprocess.run(full, cwd=cwd, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace").strip()
    return p.returncode, out


def valid_repo_name(s):
    if not s or len(s) > 100:
        return "name must be 1-100 characters"
    ok = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if any(ch not in ok for ch in s):
        return "name may only contain letters, numbers, '.', '_' and '-'"
    if s[0] == "-" or s[-1] == "-":
        return "name cannot start or end with a hyphen"
    if ".git" in s:
        return "name cannot contain '.git'"
    return None


# ------------------------------- main flow ----------------------------------

def main():
    if os.name == "nt":
        os.system("")  # unlocks ANSI colour codes in the Windows console

    global AUTO_YES
    positional, private_flag = [], False
    for a in sys.argv[1:]:
        if a in ("-h", "--help"):
            print(__doc__)
            return
        if a == "--private":
            private_flag = True
        elif a == "--yes":
            AUTO_YES = True
        elif a.startswith("-"):
            print("unknown option: %s (try --help)" % a)
            return
        else:
            positional.append(a)

    color = C()
    print(color.bold("push_to_github.py") + " - one command: folder -> new GitHub repo")
    print()

    # 1. where are we?
    cwd = os.getcwd()
    rc, top = run(["git", "rev-parse", "--show-toplevel"])
    root = top if (rc == 0 and top) else cwd
    default_name = os.path.basename(os.path.normpath(root)) or "my-repo"

    if len(positional) > 1:
        print("usage: push_to_github.py [repo-name] [--private] [--yes]")
        return
    suggested = positional[0] if positional else default_name

    rc, _ = run(["git", "--version"])
    if rc != 0:
        die(color, "Git was not found. Install it from https://git-scm.com "
                   "(or run: winget install Git.Git), then open a new terminal.")

    # 2. ask the questions
    step(color, 1, 5, "Project folder: %s" % root)
    name = ask("Repository name", suggested).strip()
    err = valid_repo_name(name)
    if err:
        die(color, "invalid repo name: %s" % err)
    private = private_flag or (not AUTO_YES and yes("Create a PRIVATE repository? "
                                                    "(public otherwise)", False))

    print()
    print(color.bold("You're about to:"))
    print("  - create github.com/<you>/%s   (%s)" % (name, "private" if private else "public"))
    print("  - commit everything in:  %s" % root)
    print("  - push it there")
    print()
    if not yes("Do it?", True):
        print("Aborted - nothing was changed.")
        return

    # 3. verify token
    step(color, 2, 5, "Verifying GitHub token...")
    _, token = load_credentials()
    user = api_user(token)
    login = user.get("login", "?")
    print("  connected as %s" % color.green("@" + login))

    # 4. create the repo
    step(color, 3, 5, "Creating repository '%s'..." % name)
    repo = api_create_repo(token, name, private)
    html_url = repo.get("html_url", "https://github.com/%s/%s" % (login, name))
    print("  %s" % color.green(html_url))

    # 5. git: init / commit / push
    rc, _ = run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root)
    if rc != 0:
        step(color, 4, 5, "Initialising git repository...")
        rc, _ = run(["git", "init", "-b", "main"], cwd=root)
        if rc != 0:  # older git without -b
            run(["git", "init"], cwd=root)
            run(["git", "symbolic-ref", "HEAD", "refs/heads/main"], cwd=root)
        print("  git init done (branch: main)")

    rc, branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    if rc != 0 or not branch or branch == "HEAD":
        branch = "main"

    # commit identity: reuse what's configured, else GitHub noreply identity
    rc, git_name = run(["git", "config", "user.name"], cwd=root)
    rc2, git_email = run(["git", "config", "user.email"], cwd=root)
    if rc != 0 or not git_name:
        run(["git", "config", "user.name", user.get("name") or login], cwd=root)
    if rc2 != 0 or not git_email:
        run(["git", "config", "user.email",
             "%s@users.noreply.github.com" % (
                 "%d+%s" % (user["id"], login) if user.get("id") else login)], cwd=root)

    # node_modules guard (the classic 500MB mistake)
    nm_dir = os.path.join(root, "node_modules")
    gi_path = os.path.join(root, ".gitignore")
    gi_text = ""
    if os.path.isfile(gi_path):
        try:
            with open(gi_path, encoding="utf-8", errors="replace") as f:
                gi_text = f.read()
        except Exception:
            pass
    if os.path.isdir(nm_dir) and "node_modules" not in gi_text:
        if yes("node_modules/ found in the project - ignore it so it doesn't get "
               "pushed? [Y/n]", True):
            with open(gi_path, "a", encoding="utf-8") as f:
                if gi_text and not gi_text.endswith("\n"):
                    f.write("\n")
                f.write("node_modules/\n")
            print("  added 'node_modules/' to .gitignore")

    step(color, 4, 5, "Staging and committing files...")
    run(["git", "add", "-A"], cwd=root)
    rc, status = run(["git", "status", "--porcelain"], cwd=root)
    changed = [l for l in status.splitlines() if l.strip()]
    rc_head, _ = run(["git", "rev-parse", "--verify", "HEAD"], cwd=root)
    has_commits = rc_head == 0
    if not changed:
        if not has_commits:
            die(color, "nothing to commit - the folder is empty (or .gitignore "
                       "hides everything).")
        print("  nothing new to commit, pushing existing commits.")
    else:
        msg = "Initial commit" if not has_commits else "Update before push (push_to_github.py)"
        rc, out = run(["git", "commit", "-m", msg], cwd=root)
        if rc != 0:
            die(color, "git commit failed:\n%s" % out)
        print("  committed %d file(s)  [%s]" % (len(changed), msg))

    remote_url = "https://github.com/%s/%s.git" % (login, name)
    rc, existing = run(["git", "remote", "get-url", "origin"], cwd=root)
    if rc == 0 and existing:
        if not yes("A git remote 'origin' already points at:\n  %s\n\n"
                   "Replace it with the new repo %s? [Y/n]" % (existing, name), True):
            die(color, "aborted - remote not changed, nothing was pushed.", 0)
        run(["git", "remote", "set-url", "origin", remote_url], cwd=root)
    else:
        run(["git", "remote", "add", "origin", remote_url], cwd=root)

    step(color, 5, 5, "Pushing to GitHub... (this can take a while for big projects)")
    # Push with the token embedded in a ONE-SHOT url: this is the only way to
    # be 100% sure Windows' Git Credential Manager doesn't pop up its
    # "username / password" dialog. The url is used for this single command
    # only - it is never written to your project or remembered anywhere.
    token_url = "https://x-access-token:%s@github.com/%s/%s.git" % (token, login, name)
    rc, out = run(["git", "push", token_url, "HEAD:refs/heads/%s" % branch], cwd=root)
    if rc != 0:
        die(color, "git push failed:\n%s\n\nUsual suspects: token lacks the 'repo' "
                   "scope, no internet, or a file is too large for GitHub "
                   "(100 MB limit)." % out)
    # Wire up the clean 'origin' remote so a plain 'git push' works later,
    # without the token stored in it.
    run(["git", "fetch", token_url,
         "+refs/heads/%s:refs/remotes/origin/%s" % (branch, branch)], cwd=root)
    run(["git", "config", "branch.%s.remote" % branch, "origin"], cwd=root)
    run(["git", "config", "branch.%s.merge" % branch, "refs/heads/%s" % branch], cwd=root)

    print()
    print(color.green("Done!  ") + color.bold(html_url))
    print("Branch '%s' is now tracking origin/%s." % (branch, branch))
    print("(If git ever asks for a GitHub username in the future: type your")
    print(" username and paste the same token as the password - Windows remembers it.)")
    if yes("Open it in your browser? [Y/n]", True):
        webbrowser.open(html_url)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted - nothing was pushed.")
        sys.exit(130)
