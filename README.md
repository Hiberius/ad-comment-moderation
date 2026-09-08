# Ad Comment Moderation

**An Agent Skill for the comments under your Facebook and Instagram ads. A rule engine
that states a reason for every verdict, keeps honest criticism visible, and tells you
where the comments on a dark post actually live.**

[![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f.svg)](LICENSE)
![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)
![Zero dependencies](https://img.shields.io/badge/dependencies-0-6E56CF)

```bash
npx skills add Hiberius/ad-comment-moderation
```

---

## It decides, it does not just delete

```bash
python3 scripts/modrules.py test comments.csv
```
```
WOULD HIDE             Buy cheap followers at crypto-x(dot)com now
                       Links: contains an obfuscated link: 'crypto-x(dot)com'
WOULD HIDE             🔥🔥🔥🔥🔥🔥🔥
                       Emoji flooding: carries 7 emoji, threshold 6
WOULD HIDE             check my profile
                       Known spam and scam phrases: matched the term 'check my profile'
WOULD HIDE             Chiamami al +39 333 1234567
                       Contact details: contains a phone number
WOULD KEEP             Honestly the last bag was stale and shipping took nine days.
WOULD KEEP             Servizio PESSIMO non comprate qui
WOULD KEEP             Quanto costa la spedizione in Sicilia?

10 comment(s): 6 would be hidden, 4 kept
This is a dry run. Nothing was sent anywhere.
```

The two complaints stay visible. No rule matches them, and a moderation tool has no
business hiding a comment it cannot give a reason for.

```bash
python3 scripts/modrules.py explain "Servizio PESSIMO non comprate qui"
```
```
verdict   WOULD KEEP
reason    no rule matched

rules evaluated, in the order they ran:
    -   Links
    -   Contact details
    -   Known spam and scam phrases
    -   Emoji flooding
    -   Empty or single-character comments
```

## Where ad comments actually live

The thing that stops most people before they start: a comment on your ad is attached to
the **page post** behind the creative, not to the ad. For a dark post, that post exists,
is reachable, and never appears on your page.

```
ad ──► adcreative ──► effective_object_story_id ──► "{page_id}_{post_id}" ──► /{post_id}/comments
```

One post often backs many ads, so you moderate the post, not the ad. Instagram comments on
the same creative are a separate thread reached through the Instagram media id.

## Allow rules run first, always

Seven rule kinds — `keyword`, `regex`, `link`, `contact`, `emoji_spam`, `min_length`,
`author_allow` — each with an action (`hide`, `flag`, `allow`) and a priority.

Allow rules are evaluated before everything else. An allow list that can be outranked by a
higher-priority hide rule is not an allow list, and this ordering is why a customer cannot
be hidden by a rule someone added in a hurry.

## Dry run, then flag, then hide

`flag` records a verdict and writes nothing anywhere. Add every new rule as `flag`, let it
run for a day on real comments, read what it caught, and only then switch it to `hide`.
Skipping that is how a moderation tool hides its first customer.

## Documentation

- [`SKILL.md`](SKILL.md) — the skill itself, what the agent reads
- [`references/rule-design.md`](references/rule-design.md) — the seven kinds, ordering, tuning for lead gen, competitor poaching and impersonation rules, false positive discipline
- [`references/meta-graph-comments.md`](references/meta-graph-comments.md) — dark posts, hide vs delete, pagination, rate limits, token handling, comments as untrusted input

## A working implementation

[CommentHide](https://github.com/Hiberius/commenthide-facebook-comment-moderation) is the
full thing: a single Cloudflare Worker with D1, a dashboard, a dry-run inspector and
one-click undo, MIT. This skill is the reasoning behind it, usable on any stack.

## Not for burying criticism

The starter rules keep unhappy customers visible on purpose. Hiding them does not work
either: they escalate, screenshot, and post again somewhere you cannot reach.

## License

MIT. No network calls, no telemetry, no dependencies.
