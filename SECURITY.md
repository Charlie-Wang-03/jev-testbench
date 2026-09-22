# Security

## What this repository actually is

A local measurement harness that talks to the TypeSafe API. That gives it three properties worth a
security page, and they are the whole of the surface:

1. It uses a **real credential**, stored as a plaintext file on the machine that runs it.
2. Its live commands **spend real money** against a real account.
3. It writes the **full `state` of every request** into a plain-text log that is committed to git.

Everything else here is inert on purpose. Every handler in the routing experiment returns a fixed
dict, records `side_effect: False`, and reaches nothing — the module says "Reads nothing" and
"Contacts nobody" and that is meant literally ([src/jev_lab/routing.py](src/jev_lab/routing.py)).
No case carries real personal, customer, or proprietary data; all state is synthetic. The test
suite blocks sockets outright, so a test that reached for the network fails instead of spending.

The risks below are therefore about the credential and the log, not about the code running
somewhere hostile.

## Reporting a vulnerability

**There is no security email address, and this file does not invent one.** Use one of these:

- **Preferred:** GitHub's private vulnerability reporting on this repository — *Security* tab →
  *Report a vulnerability*. If the option is not shown, it has not been enabled yet, so fall back
  to the next item.
- Otherwise, open a regular issue saying only that you have a security report and how to reach you.
  Keep the details, and anything credential-shaped, out of the issue.

**Never paste an API key into an issue, a pull request, a commit, a branch name, or a comment.**
If a key of yours may have been exposed, revoke it in the TypeSafe Console **first** — see
[If you think a key is exposed](#if-you-think-a-key-is-exposed).

## Risks, roughly in the order they are likely to bite

### 1. The API key is a plaintext file on disk

`.secrets/typesafe.env` holds a live key in cleartext. It is gitignored, and
`git check-ignore -v .secrets/typesafe.env` is the check that proves it — not a comment in a doc.

What that does **not** buy you: the file is readable by anything running as you, by backup and
indexing tools, and by cloud-sync agents if the repository sits in a synced folder. On Windows the
file inherits its ACL from the parent directory, which on a default machine means `Administrators`,
`SYSTEM`, `Authenticated Users`, and `BUILTIN\Users` (read) — approximately "you, plus anything
running elevated," but **not** a per-user lock. This repository does not manage that ACL. See
[docs/guides/credentials.md](docs/guides/credentials.md) for the full account.

### 2. Publishing from a directory copy instead of from git

This is the most practical way a key escapes, and it does not involve a bug in anything.

`.secrets/` is untracked, so **no git operation can publish it** — not `push`, not `archive`, not
`clone`. A `zip`/`Copy-Item`/Explorer-drag of the working directory is a different matter: it ships
`.secrets/typesafe.env`, and also `.venv/`, `dist/`, and the ignored files under `results/`.

**Publish from git.** Push the branch, or produce an archive with `git archive`, and let the
clone be the thing people see. If you must copy a directory, copy a fresh clone.

### 3. The log records the full state of every request

`results/usage.jsonl` is committed, and each record carries the `state` that was sent plus every
answer returned. That is the point of the repository — the log is the evidence — but it means a
`state` containing something private would become public the moment the log is. All cases here are
synthetic, and the repository requires that they stay that way. Keep it that way in any new
experiment.

### 4. Debug logging dumps request and response bodies

**Do not set `TYPESAFE_LOG_LEVEL=debug` while running experiments.** The SDK redacts secret
*headers* but explicitly does **not** redact request or response *bodies*, so debug output prints
your complete `state` and every answer, straight into a terminal scrollback or a log file. Nothing
in this repository sets it. If you need it to debug the SDK itself, do it on a synthetic payload in
a throwaway directory, and treat the output as data you have to dispose of.

### 5. A key that ever entered git history

Rewriting history does not undo an exposure: a leaked credential is compromised from the moment it
leaks, and the only thing that helps is making it stop working. So the order is revocation first,
cleanup second.

The current state is audited and clean — see [Git history audit](#git-history-audit) — but the rule
holds for the future: if a key is ever committed, revoke it, then decide whether history cleanup is
worth the disruption of rewriting a published branch.

### 6. `CLAUDE.md` is not a security boundary

[CLAUDE.md](CLAUDE.md) tells coding agents working in this repository never to read, print, copy,
or commit the credential. That is a **convention a cooperative agent follows, not a mechanism**,
and describing it as one would be a false claim about a real credential. An agent with file access
can read that file.

The boundaries that are actually mechanisms are these four, and weakening any of them is a security
change:

| Boundary | What it is |
|---|---|
| `.gitignore` | `.secrets/`, `*.env`, `*.secret`, `*.secrets`. A key cannot be committed by accident; `git check-ignore` is the proof. |
| Fail closed | A missing, empty, malformed, duplicated, or unreadable source stops the run before a request is sent, rather than proceeding on a guess. |
| No printing path | The loader has no function that returns the key for display, status strings carry no derived identifier, and `scrub_secrets` covers error text that quotes a response. |
| OS permissions | The file's ACL — which this repository does not manage. See risk 1. |

## Git history audit

The full history was scanned before this repository was assessed for publication: every commit
reachable from every ref, every blob in the object database including unreachable ones, and the
working tree. The result was clean — no credential, key, or token in any object. The one finding
was the expected one: the local `.secrets/typesafe.env`, flagged as a generic API key, gitignored
and untracked, and therefore not publishable by any git operation. No file matching `*.env`,
`*.secret`, or `*.secrets` has ever been committed; `.secrets.example/typesafe.env` is the
committed template and holds an obvious placeholder.

The limits of that audit matter as much as its result:

- It is a **snapshot**, taken at `ab03f96`. Commits after it are unaudited. The scan is cheap and
  should be re-run before the repository is made public.
- It covers **local git objects only**. GitHub's own copies, pull-request refs, and anything pushed
  from another machine are not visible to a local scan.
- The scanner ran with its default rule set — no custom rules, default decode depth.
- The contents of `.secrets/` were **not** read. Only its existence, ignore status, and untracked
  status were checked, via git plumbing. That is deliberate, and it is why this page describes how
  the file is handled rather than what is in it.

## If you think a key is exposed

Committed, pasted, synced, screenshotted, or printed into a log — the remedy is the same:

1. **Revoke the key in the TypeSafe Console and issue a new one. Do this first.** Everything else
   is secondary, and history rewriting is not a substitute for it.
2. **Then** replace it: update `.secrets/typesafe.env` or the session variable, and check whether
   the exposure reached logs, CI output, or a synced folder.
3. **Then**, if it entered a commit, consider cleaning history — after revocation, and on purpose.
   Rewriting published history is disruptive and does not undo step 1.

## Supported versions and scope

There are no releases and no maintained branches: `main` is the only line, and fixes land there.
Issues in the TypeSafe SDK or the TypeSafe service itself are TypeSafe's to handle, not this
repository's. Issues in GitHub's platform are GitHub's. Everything about how *this* repository
handles its credential, its log, and its budget is in scope here.
