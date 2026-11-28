# Code standards

These rules come from what PR reviews keep asking for. A reviewer checks
each one, and a PR that doesn't meet one gets a comment saying which.

## What a change contains

| Rule | What a reviewer looks at |
| --- | --- |
| A change does only what its goal needs. | Every change in behavior has a reason. Unrelated refactors, extra features and policy changes go in a PR of their own. |
| A fix covers exactly the cases it means to. | Which cases change, and which neighboring ones stay the same. Different errors are not handled as one. |
| A change holds on the whole path. | Follow it from the user's input to the end result, through the callers, the state it changes and the side effects. One correct function doesn't make the whole operation correct. |
| A fix reaches every sibling of the bug. | Grep for the same pattern: every subcommand, guard of the same shape and caller of a changed predicate gets the fix in the same change. That includes the other branches of the same operation and the other messages that name the same endpoint or rule. |
| A change re-derives everything built on what it changes. | When a change alters a formula, a list, a layout breakpoint or the timing of an async step, find every caller, saved copy and test that assumed the old meaning, and run it. |
| A failed read, parse or hash means "unknown". | It never means "empty", "none" or "equal". Keep what was read before, copy a file that doesn't parse aside before writing over it, and fix the shared reader rather than writing a strict one beside it. A list that guards access (an allow list, a key limit) fails closed when its file can't be read. Test with the file unreadable. |
| Another app's values come from that app. | When writing another app's file or speaking for it, take each field's type and value from that app's own data, binary, merge code or docs, not only its field names. |
| Nothing that can block runs under a lock its reader needs. | Never send on a channel or call anything that can block while holding a lock the receiver takes first. Set shared state before the handoff that lets another thread look at it, and a struct copied by value that holds a map is not a copy. A fake server's handler runs on many threads: guard what it records with a lock, and count only the calls the test makes, since background reads reach it too. A change that starts a thread or timer runs under the race detector before it is pushed. |
| A default never overrides a value the user set. | Before writing a key, list everywhere that setting is read from, and test with a user-set value present. A migration that rewrites a setting names the users who set it themselves, and leaves their value alone or says in the release why not. |
| A size budget is met, not raised. | A change that reaches a budget moves something out first: to a lazily loaded file or code it replaces. A raise names what the owner agreed to, not "nothing left to move". Comments are not what gets cut: the budget counts code. After a rebase, run the budget test again at the pushed head. |
| Checks cover the edges the change touches. | For numbers, check the boundaries. For paths, check each platform. For concurrency, check races and stale state. Pick checks by risk. |

## Tests

| Rule | What a reviewer looks at |
| --- | --- |
| A fix comes with a test that fails without it. | The reviewer puts the old code back and runs the test, and the test must fail. A PR description says what it failed with. A test named for a guarantee goes red when that guarantee is broken by hand. |
| A test never reaches the network. | A vendor's page or API is served from a local test server, built from bytes saved from the real one. A package comes from a lock file, not a registry's latest. Break the change and watch where the test's requests go. |
| Tests use real inputs. | Fixtures look like real requests, real serialized output and real files on disk. That includes missing fields, empty values and defaults. |
| Tests check behavior, not implementation. | Assert what the user or caller needs. Formatting changes and internal refactors shouldn't break a test, unless exact bytes are the requirement. |
| A test that fails on `main` is a bug to fix now. | "Fails the same on origin/main" is not a baseline, and neither is "fails under the full run, passes alone". Fix it at its cause, or open an issue naming the cause, in a commit of its own, before shipping on top of it. Run a test 20 times under the race detector before calling it a flake. |
| A red's issue is read to its last comment, and a patch on it is taken first. | Before filing, commenting on or shipping past a red, search its test's name and read every comment. "Seen again" is not work on it: take it, or say who has it. A patch posted there is reviewed and ported before anyone writes another. |
| A check that a value is gone looks past text the program or the test made up. | A substring check strips placeholders and stand-ins first, or looks for a value no port, id, time, hash or random name can spell (letters only, longer than a few characters). |
| Tests stay out of the real machine. | Run them under a temp HOME. Never touch a real config. |
| Whatever a test starts ends when the test does. | A fake process, a thread or an async refresh a test sets going is stopped or waited for before the test returns, or it writes into the next test's folder ("directory not empty") or spins for days. |
| One full suite runs on a machine at a time. | A full suite waits for the one already running on that machine, and a record from a run beside another suite is not a pass. Its reds are named with an issue each, not "files this change doesn't touch". |
| A record is written once its run has ended. | A body names the result of a run that finished: "still running at push" or "N in, M red when this was written" is not a record, and every red in it is named with its issue. |
| A timing test leaves room on both sides. | Never bound a test by wall-clock time a loaded runner can exceed, and keep a threshold classifier's fixture far from every threshold it has. Reproduce a timing failure by injecting the delay (a held write, a late first arrival), not by rerunning until it fails, and list every timing assumption in the test when fixing one. |

## Acceptance criteria

A change is merged or released only when it shows each of the following.
Say which ones were run and what they printed. A check that wasn't run is
listed as not run, never left out.

1. **A test that fails without the change.** Put the old code back and run
   the new test. It must fail with a real `FAIL` that names the behavior. A
   compile error or a skipped test doesn't count. Say which test fails and
   what it failed with. Then restore the change and check the test passes.
2. **Tests in a sandbox.** Run tests under a temporary HOME with the
   dependency caches pinned: without them, every run downloads its
   dependencies again into the new temp HOME. A test never reads or writes
   a live config.
3. **The build and the suite.** Run the formatter on the changed files (it
   prints nothing), the static checks, the build and the tests. In a chain of
   commands, set `set -o pipefail`, so that
   `<test command> | tail && git push` stops on a failure. Run everything, not
   the packages you think you touched: the repo's guard tests live in packages
   a change doesn't touch. A guard that keeps being missed gets a twin in the
   package the change runs.
4. **Real use where possible.** A change to an outside service is also
   checked against the real thing: a real account or key, the real config
   format, the vendor's real reply. Do this in a sandbox HOME with copies
   of the credentials. Never touch a live service. If a real check isn't
   possible, say so. What wasn't tried with the real thing isn't built on
   and isn't told to users as working. A platform report is checked on
   that platform, and a build for that platform is not a test. A test of
   a guard goes through the real stack or the built binary. When the
   guesses about a vendor differ, design the check that tells them apart,
   or ask the reporter to run it.

A PR is merged only after a maintainer has pulled it, merged it onto
current `main` and run the checks above on the result. The merge names the
commit that was reviewed: `gh pr merge --match-head-commit <reviewed sha>`.
A push made during the review then stops the merge, rather than shipping
code nobody ran. A head pushed after the review is reviewed again, and the
comment names the new head. Write on the PR what was run, at which head,
and then merge: a merge with no record of what was run can't be checked
afterwards. A Draft PR can't be merged until it is marked Ready for review.

## Reviewing a PR

These patterns come from recent reviews. A reviewer checks each one that
applies:

- **Run it.** Pull the head, merge it onto current `main` (resolving
  conflicts if needed) and run the acceptance checks. Reading the diff alone
  isn't a review.
- **Break it on purpose.** Revert the fix, or break the code it guards in
  several ways, and check that the new tests catch each break. A reviewer
  may add review tests of their own.
- **Check the vendor, not the PR's account of it.** Read the upstream source
  for a vendor's behavior. Try the change against a real upstream.
- **Check each platform and architecture.**
- **Follow the whole path.**
- **Classify narrowly.** A mark or error class covers only the case it
  describes.
- **A preview writes nothing.** A dry run, plan or preview has no side
  effects.
- **Don't reverse deliberate decisions.** Product decisions are the
  maintainer's to change. A PR that changes one is left for the maintainer.
- **Test suites.** Compare pass counts with `main`. A test that fails on
  `main` too is not a baseline (see [Tests](#tests)). A PR that says its
  failures "fail the same on origin/main" gets that checked, and gets them
  fixed or filed before the merge.
- **Docs match the source.** A reference is checked against the code it
  links, and every link must resolve.
- **Keep the PR to its goal.** Unrelated tests and refactors go in a PR of
  their own. Comments name functions, not line numbers. Fixture names match
  what they stand for.

## Comments

- A comment says what the code is for, in a sentence or two. Name functions
  instead of giving line numbers, which go stale.

## Commits

A commit message names the areas it changes, then says what the user now
sees, written as plain behavior. Give the issue number or the reporter. The
body says how it was verified, and which test fails without the change.

The record of what was run is in the commit body, where a later review can
read it: not in push notes, a chat or only on the PR. A large commit with
no body can't be reviewed afterwards. When a community commit is applied
without a body, the review commit says what was run against that author's
code.

One commit has one goal. Two reports fixed together are two commits,
each with its own record, so a revert takes back one and keeps the other,
and a review can tell which test guards which change. A fix found on the
way goes in a commit of its own.

A checkout, a worktree and the logs in it belong to the session that made
them. Work in a worktree of your own (`git worktree add --detach`), never
check out, commit from or clean another session's, and after committing
check that `git show --stat HEAD` lists your files and only yours.

A commit's tree is origin/main plus its own change. A file in its `--stat`
that the change never meant to touch, or a test file going out, is a stale
tree taking out someone else's work: stop, rebase or cherry-pick onto
origin/main, and never commit files copied from an older checkout. A
review checks `git diff <commit>^ <commit> --stat` against the subject.
