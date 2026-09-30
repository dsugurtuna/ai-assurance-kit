# Why it's built this way

Unofficial; not government guidance. This page explains the reasoning behind ai-assurance-kit's design, for anyone deciding whether to use it, adapt it or argue with it.

## The problem in two sentences

Organisations are told to assure AI "proportionately", but the usual tool is a long document that cannot be compared, checked for gaps or re-checked when the system changes. So light use cases wait as long as risky ones, and risky ones drift after approval without anyone noticing.

## Principles the checks draw on

Some checks cite these working principles as well as public guidance. They are the project's own, not quotations from any source.

- **Read freely, write carefully.** Reading and drafting can be checked afterwards. Sending and writing change things outside the tool, so they need stronger controls.
- **Permission to build is not permission to deploy.** Building, connecting data, granting access, sharing a tool and operating it are separate decisions, often for different people.
- **Usage is not quality.** How often a tool is used says nothing about whether its outputs are right.
- **A second model is a critic, not a verifier.** Model grading can find problems. Agreement between models is not verification.
- **Fix the data before adding an agent.** Many problems brought to AI are better solved by fixing the data or the process, or by ordinary automation.
- **Measure total human effort.** Count the time spent checking and correcting outputs, not just the time saved generating them.
- **Make uncertainty visible.** Say what is unknown or unverified rather than filling the gap with a guess.

## Design choices

**Why a structured record rather than a form or a document?**
Because structure is what makes everything else possible. A YAML file in git can be validated, checked, diffed, reviewed in a pull request and aggregated into a register. A document can only be read. YAML is also readable by people who do not write code, which matters because the business owner, not the developer, should be able to read the record.

**Why reject unknown fields?**
Because a typo such as `personal_date: true` would otherwise be ignored, and the record would say less than its author thinks. Failing loudly on unknown fields is cheap; a silently missing answer is expensive.

**Why prompts, not verdicts?**
Because the kit only sees what the record says. Whether a DPIA is required, whether a tool is in ATRS scope, or whether a risk is acceptable are decisions for accountable people with context the kit does not have. A tool that says "compliant" invites people to stop thinking. So each result says what to record or decide next, severity says how soon, and `aiak check` exits 0 unless a team deliberately gates on a severity with `--fail-on`.

**Why small rules in plain Python, not a rules language or a model?**
Because each rule needs to be readable by a reviewer, testable in isolation and deterministic. Twenty-six short functions with metadata are easier to audit than a rules DSL, and far easier than a model whose judgement would itself need assuring. Every rule has a test that makes it fire, and a tidy record in the tests fires none of them.

**Why does every rule cite sources, and only from a fixed list?**
Because a reviewer should be able to ask "why is this prompt here?" and follow the answer to a document. Restricting citations to a checked list in `sources.py` (including the exact NIST AI RMF subcategory text) stops the crosswalk drifting into claims nobody checked. A citation means "this source makes the prompt worth asking", never "this source requires it".

**Why an ordered action mode?**
Because "what can it do?" is the question that most changes the level of scrutiny. `read_only` < `drafts` < `writes_with_approval` < `autonomous` lets the checks spot sends without approval, and lets `aiak diff` recognise a move from drafts to autonomous sends as material, not as a text edit.

**Why record permissions separately from the action mode?**
Because the action mode is what the team says the system does, and permissions are what it can do. The gap between them is unused power that a fault, a prompt injection or a later change can use. `AIAK-ACT-003` looks for that gap.

**Why separate decisions for build, connecting data, access, sharing and going live?**
Because one approval is often read as covering the next. Recording each decision, with who took it and when, makes the gap visible: a record whose status is `live` but which only has a build approval gets a prompt.

**Why compute levels from named features and a policy file?**
Because proportionality is an organisational decision, not a property of the code. The kit provides the mechanism (fourteen documented features and a small condition language) and the organisation provides the policy. Named features are easy to review and explain to a governance board; arbitrary expressions would not be. Every trigger that fires is shown, so the level is never a bare label.

**Why is the bundled policy only an example?**
Because risk appetite and review thresholds must be set by whoever is accountable for them. The example's numbers (an appetite of 9 on a 1 to 25 scale, a 2x scale-change threshold) are there to demonstrate the mechanism. The file, its name and its policy label all say "example" so nobody mistakes it for a standard.

**Why a diff with a short list of material changes?**
Because the riskiest moment in a use case's life is often after approval, when data, connectors, recipients or autonomy are added one small step at a time. A generic diff shows everything that moved; the material-change rules say which moves should reopen review, and why. Treating every change as material would make people ignore the flag.

**Why role titles required and names optional?**
Because published transparency records name roles rather than people (the ATRS guidance asks for the senior responsible owner as a role title, for continuity and security), while internal assurance sometimes needs names, for example to notice that the builder is also the assurer. `--redact-names` produces a card that shows roles in place of the name fields (it cannot find names typed into free text).

**Why borrow the AQuA Book's roles?**
Because the separation between the person who builds something and the person who assures it is well established in analytical quality assurance, and it applies directly to AI systems. The kit maps business owner, builder, assurer and approver onto the AQuA commissioner, analyst, assurer and approver, and adds a maintainer because AI systems keep changing after launch.

**Why no model anywhere in the kit?**
Because an assurance tool should give the same answer for the same record every time, offline, with nothing to configure. A model could help people draft records one day, but it will never sit in the check path.

**Why a card and a register as the outputs?**
Because the people who need to act on assurance read one page, not a YAML file. The card puts the level, the prompts and the risks where a business owner will see them. The register lets a governance lead see the whole portfolio at once, including which reviews are overdue.

**Why a standalone HTML card with no JavaScript?**
Because cards get emailed, printed and archived. A single file with inline styles, semantic structure, text labels as well as colour, and print styles works in all of those places, and the tests check the basics of accessible structure (page language, one main landmark, table header scope).

**Why `--today`?**
Because "review overdue" depends on the date. Fixing the date makes cards and registers reproducible, so they can be regenerated byte for byte and used as snapshot tests.

## Questions worth asking

**"A record can say anything. Isn't this just box-ticking with extra steps?"**
Partly, and the kit is open about it: it checks the record, not the system. What it changes is the cost of vagueness. Claims become explicit fields that a reviewer can challenge line by line, evidence has a date, a kind and a performer, independence is recorded rather than assumed, and a diff shows exactly what changed since the last approval. The rules that look for missing evidence, same-person assurance and model-only grading exist because those are the common ways a record looks complete while saying little. The verification itself still has to be done by a person, which is why the output is a list of prompts and not a score.

**"Your risk matrix and levels are arbitrary. Why should anyone trust an appetite of 9?"**
They should not, and the kit does not ask them to. The numbers are labelled as an example everywhere they appear. The contribution is the mechanism: a versioned policy file that states the appetite, the levels and the triggers explicitly, and a result that always shows which trigger raised the level and why. Likelihood x impact on 1 to 5 scales has known weaknesses (ordinal scores multiplied together, coarse bands); the kit uses it because it is familiar, and puts the owner, the controls and their status next to the score so the number is never the whole story. Qualitative ratings are on the roadmap.

**"Guidance changes. How do you stop the checks drifting from the sources they cite?"**
Three ways. First, citations can only come from a fixed list in `sources.py`, and NIST AI RMF subcategories are stored with their checked text, so a rule cannot cite something nobody looked at. Second, the rules reference and the checks crosswalk are generated from the code, and tests fail if the committed docs differ. Third, [SOURCES.md](SOURCES.md) records how each source was checked, when, and what remains unverified, so a maintainer knows where to look when guidance is updated. Because the rules are phrased as prompts that cite "relevant" guidance, a change in guidance usually means rewording a prompt, not unpicking a compliance claim.

**"Why not let an LLM fill in the record, or review it?"**
Drafting help could be useful later, as long as a person owns every answer. Review by a model is a different matter: it would make the check path non-deterministic and add a component that itself needs evaluating. A second model is a critic, not a verifier. The kit's checks stay deterministic so that their behaviour can be tested and explained.

## What's next

- Export a draft ATRS-shaped skeleton from a record, keeping unknowns visible, to shorten the path from internal assurance to publication.
- Attach evidence files by hash, and import results from evaluation harnesses, so "evidence" on the card links to something checkable.
- A GitHub Action and pre-commit hook, so a repository of records gets checks and material-change flags on every pull request.
- Qualitative risk ratings as an alternative to likelihood x impact.
- Support for systems with several components, each with its own data and actions.
