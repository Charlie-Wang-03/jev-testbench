# Credentials

**English** | [简体中文](credentials.zh-CN.md)

This repository used a real TypeSafe API key during its live runs. This page describes how that key
is resolved, and — more usefully — what the scheme does **not** buy you.

> **Read this first:** the rules in this document and in [CLAUDE.md](../../CLAUDE.md) are
> **conventions that a cooperative agent follows. They are not a security boundary.** An agent or a
> program with file access can read `.secrets/typesafe.env`. Saying otherwise would be a false
> claim about a real credential. See [SECURITY.md](../../SECURITY.md) for the boundaries that
> actually exist.

---

## 1. Resolution order

The key is read from exactly two places, in this order, and from nowhere else:

1. the environment variable **`TYPESAFE_API_KEY`**, when it holds a non-blank value;
2. **`<repo>/.secrets/typesafe.env`**, a local file that is git-ignored;
3. neither — and every command that needs the API stops before spending anything.

The environment wins, so a rotated or one-off key can be set for one terminal without touching the
file. **When the environment holds a value, the file is not read at all** — a broken file cannot
take down a session that was configured explicitly.

The loader **fails closed**. An absent, empty, malformed, duplicated, or unreadable source stops
the run *before* a request is sent, rather than proceeding with a guess.

## 2. What a command will tell you about your key

No command ever prints the key, its length, a prefix, a suffix, or a hash of it. Every command that
touches credentials reports exactly one of:

```text
TYPESAFE_API_KEY: missing
TYPESAFE_API_KEY: exists (source=environment)
TYPESAFE_API_KEY: exists (source=local-secret-file)
TYPESAFE_API_KEY: unusable (malformed | duplicate-key | unreadable)
```

There is no code path that returns the key for display, and no status string carries a derived
identifier. That is deliberate: a design with no printing path is what makes "never reveal" true
rather than aspirational.

## 3. Setting a key for one session

Without leaving it in your shell history:

```powershell
$secureKey = Read-Host "Paste TypeSafe API key" -AsSecureString
$env:TYPESAFE_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
Remove-Variable secureKey
```

## 4. The persistent local file

A session variable disappears when the terminal closes. To avoid re-pasting a key, put it in
`.secrets/typesafe.env` — inside the working directory, and outside version control.

The format is one line, no quoting, no shell syntax:

```text
# Local credentials for this machine. Never commit this file.

TYPESAFE_API_KEY=<your-key>
```

Blank lines and `#` comments are ignored; the value is everything after the `=` with surrounding
whitespace removed. **Nothing in the file is expanded, substituted, or executed** — `$(...)`,
`${VAR}`, backticks and quotes are ordinary characters, and there is no inline-comment syntax (a
trailing `# comment` becomes part of the value). Two `TYPESAFE_API_KEY` lines, an unexpected name,
or a line that is not an assignment is an **error rather than a silent choice**, and the loader
stops. An empty value means *missing*.

`.secrets.example/typesafe.env` is the committed template and holds an obvious placeholder
(`YOUR_TYPESAFE_API_KEY_HERE`). `.secrets/` is not committed:

```console
$ git check-ignore -v .secrets/typesafe.env
.gitignore:28:.secrets/    .secrets/typesafe.env
```

`git add --dry-run .secrets/typesafe.env` is refused for the same reason, and
`git add --dry-run .secrets.example/typesafe.env` succeeds — the template is meant to be committed.

---

## 5. What this scheme does and does not buy you

It keeps the key **out of Git, out of the diff, and out of the chat transcript.** It is still a
plaintext file on disk. Be clear-eyed about that:

- It is appropriate for a **personal experiment repository on a machine you control** — not for a
  shared host, and not as a model for production secret management.
- It is readable by **anything running as you**, and by backup, indexing and cloud-sync tools that
  watch the directory — OneDrive, Dropbox and Windows Search included, if the repo is inside a
  synced folder.
- The default Windows ACL on the file inherits from its parent: `Administrators`, `SYSTEM`,
  `Authenticated Users`, and `BUILTIN\Users` (read). On a single-user machine that is roughly "you
  and anything running as an administrator", but it is **not a per-user lock**, and a second local
  account can read the file. This repository does not manage that ACL. Tightening it is optional,
  and if you do it, do it on **the file** — not on the repository directory, and not in a way that
  drops `SYSTEM` or your own account.
- **An agent with file access can read it.** [CLAUDE.md](../../CLAUDE.md) asks agents not to, and
  that instruction is a convention, not a mechanism.

### The four boundaries that are mechanisms

The rules above are conventions. These are not, and they are the ones to keep working when you
change anything here:

| Boundary | What it is |
|---|---|
| **`.gitignore`** | `.secrets/`, `*.env`, `*.secret`, `*.secrets`. The key cannot be committed by accident, and `git check-ignore` is the check that *proves* it — not a comment in a document. |
| **Fail closed** | An absent, empty, malformed, duplicated or unreadable source stops the run before a request is sent. |
| **No printing path** | The loader has no function that returns the key for display; status strings carry no derived identifier; `scrub_secrets` covers error text that quotes a response. |
| **OS permissions** | The file's ACL — which this repository does **not** manage. See the caveat above. |

If any of those four is weakened, the conventions above stop being enough. Treat a change to any of
them as a security change.

---

## 6. If you suspect the key was exposed

Committed, pasted, synced, screenshotted, or printed into a log — the remedy is the same:

1. **Revoke the key in the TypeSafe Console and issue a new one. Do it first.** Rewriting history
   afterwards does not undo an exposure; a leaked credential is compromised from the moment it
   leaks, and the only thing that helps is making it stop working.
2. **Then** clean up: update `.secrets/typesafe.env` or the session variable, and check whether the
   exposure reached a log, a CI transcript, or a synced folder.
3. **Then, if it was a commit**, consider history cleanup — but only after revocation, and only
   deliberately. Rewriting published history is disruptive and is not a substitute for step 1.

> **Never enable `TYPESAFE_LOG_LEVEL=debug` while running experiments.** The SDK redacts secret
> *headers* but explicitly does **not** redact request or response *bodies*, so debug logging dumps
> your full `state` and every answer. Nothing in this project enables it.

For how to report a security problem in this repository, see [SECURITY.md](../../SECURITY.md).
