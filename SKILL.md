---
name: ad-comment-moderation
description: Use when spam, scam replies, link drops or competitor poaching appear under Facebook or Instagram ads and posts - designing or debugging a comment moderation rule set, deciding what to hide versus keep, finding where comments on a dark post actually live, or building against the Meta Graph API comment endpoints without hiding real customers.
---

# Ad Comment Moderation

## Overview

Most "hide Facebook comments" scripts hide everything new. That buries genuine questions
and honest criticism along with the spam, which is why the category has the reputation it
has.

**Core principle: every verdict states a reason, and a comment nobody can give a reason
for stays visible.**

Under a lead-gen ad this is not cosmetic. Link drops send your paid traffic to a
competitor, scam replies impersonate you to people who just gave you their number, and
both sit under the ad for as long as it runs.

## When to use

- Building or tuning a comment moderation rule set for Facebook or Instagram
- Spam under an ad, and you cannot find the post it is attached to
- Deciding what should be hidden and what must not be
- Working with the Graph API comment endpoints
- A moderation tool hid a customer and you need to know why

**Not for:** burying criticism. See the last section.

## Where ad comments actually live

A comment on your ad is attached to the **page post** behind the creative, not to the ad.
For a dark post that post exists, is reachable, and never appears on your page.

```
ad ──► adcreative ──► effective_object_story_id ──► "{page_id}_{post_id}" ──► /{post_id}/comments
```

One post often backs many ads, so moderate the post, not the ad. Instagram comments on the
same creative are a **separate thread** reached through the Instagram media id: handle one
and not the other and half your delivery keeps the spam.

## Hide, do not delete

Hiding sets `is_hidden`. The comment stays visible to its author and their friends, which
is how Facebook's own hide function behaves: the author does not notice, and there is no
second conversation about censorship. Deleting removes it for everyone, the author
notices, and the next comment is about you rather than about your product.

```
POST /{comment-id}  is_hidden=true    hide
POST /{comment-id}  is_hidden=false   undo
```

## The rule engine

Seven kinds, each with an action (`hide`, `flag`, `allow`) and a priority:

`keyword` · `regex` · `link` · `contact` · `emoji_spam` · `min_length` · `author_allow`

**Allow rules run first, always.** Then everything else in priority order, first match
wins. An allow list that can be outranked by a higher-priority hide rule is not an allow
list, and this ordering is the reason a customer cannot be hidden by a rule someone added
in a hurry.

```bash
python3 scripts/modrules.py rules --starter > rules.json
python3 scripts/modrules.py test comments.csv --rules rules.json
python3 scripts/modrules.py explain "check my profile" --rules rules.json
```

Everything is a dry run. This engine decides; it talks to no platform.

## Dry run, then flag, then hide

1. Run the rule set over real comments and read the verdicts. Nothing is sent.
2. Add each new rule with action `flag`. It records a verdict and writes nothing.
3. Let it run for a day. If it flagged a customer, the rule is wrong.
4. Only then switch it to `hide`.

Skipping steps 2 and 3 is how a moderation tool hides its first customer.

## False positives cost more than false negatives

A missed spam comment is noise. A hidden customer question is a lost sale and, once the
customer notices, a public complaint.

- If you cannot phrase the reason for a rule in one clause, the rule is too vague to run.
- Review what was **hidden** weekly, not what was kept. The mistakes are there.
- Track hit counts. A rule that never fires is dead weight; a rule firing on a third of
  all comments is catching customers.

## Reference

| Topic | File |
|---|---|
| The seven kinds, ordering, tuning for lead gen, competitor poaching, impersonation | `references/rule-design.md` |
| `effective_object_story_id`, hide vs delete, permissions, pagination, rate limits, token handling | `references/meta-graph-comments.md` |

## Comment text is attacker-controlled

Render it with `textContent`, never `innerHTML`. Never interpolate it into a shell
command, a SQL string or a prompt. A comment can carry invisible Unicode and hidden
instructions: [invisible-text-forensics](https://github.com/Hiberius/invisible-text-forensics)
covers what fits inside one.

## What this is not for

This hides spam, scams, harassment and off-topic noise on posts you own, through an API
Meta provides for that purpose. It is not for burying criticism, and the starter rules
reflect that: "the last bag was stale and shipping took nine days" and "servizio pessimo,
non comprate qui" both match nothing and stay visible.

Hiding unhappy customers also does not work. They escalate, screenshot, and post again
somewhere you cannot reach. Answer them.
