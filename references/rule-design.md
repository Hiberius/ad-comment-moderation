# Designing the rule set

## The seven kinds

| Kind | Pattern | Hides when | Notes |
|---|---|---|---|
| `keyword` | comma-separated terms | a term appears as a whole word, case and accent insensitive | `perche` matches `PERCHÈ`; `dm` does not match `dming` |
| `regex` | a regular expression | it matches | an invalid expression is skipped, never fatal |
| `link` | — | a URL, a bare domain, or an obfuscation like `example(dot)com` | must not fire on `costa 12.50 euro` |
| `contact` | — | an email, an `@handle`, or a phone number | a phone needs at least eight digits |
| `emoji_spam` | a threshold | the comment carries that many emoji or more | six is a reasonable default; three is not |
| `min_length` | a threshold | the trimmed comment is shorter | catches `.` and `👍`-only noise |
| `author_allow` | names or ids | the author matches | pair with the `allow` action |

Every rule carries an **action** (`hide`, `flag`, `allow`) and a **priority**.

## Ordering is a safety property, not a detail

Allow rules run **first, always**. Then everything else in priority order, first match
wins.

An allow list that can be outranked by a higher-priority hide rule is not an allow list.
Putting allows first means a customer, a team member or a partner can never be hidden by
a rule someone added later in a hurry.

## Use `flag` before `hide`

`flag` records a verdict and writes nothing anywhere. It is how you trial a new rule on a
live thread and read the consequences a day later without having hidden anything.

The workflow that keeps you out of trouble:

1. Add the rule with action `flag`.
2. Let it run for a day on real comments.
3. Read what it caught. If it caught a customer, the rule is wrong.
4. Only then switch it to `hide`.

## Tuning for lead generation

The starter set catches generic spam. Three additions matter when you run lead ads:

- **Competitor poaching.** "scrivimi in privato", "da noi costa meno", "contattami per un
  preventivo" under your lead ad is someone harvesting the audience you paid for. The
  starter set keeps these, deliberately, because the same phrasing appears in honest
  conversation. Add them as an explicit keyword rule for your own account, and start with
  `flag`.
- **Impersonation.** Accounts replying to your commenters with a near-copy of your page
  name and a WhatsApp number. Catch them with a `regex` on the number format plus a
  keyword on your own brand name appearing in a comment that is not from you.
- **Off-topic language.** On multilingual delivery, comments in a language you do not
  serve are usually bot traffic. This is a `regex` on script ranges, and it is a rule that
  needs review, because a real customer writing in an unexpected language exists.

## False positives cost more than false negatives

A missed spam comment is noise. A hidden customer question is a lost sale and, when the
customer notices, a public complaint about censorship.

Three habits:

- **Every verdict states a reason.** If you cannot phrase the reason in one clause, the
  rule is too vague to run.
- **Review what was hidden weekly**, not what was kept. That is where the mistakes are.
- **Track hit counts per rule.** A rule that has never fired is dead weight; a rule that
  fires on a third of all comments is almost certainly catching customers.

## What this is not for

This hides spam, scams, harassment and off-topic noise on posts you own, through an API
Meta provides for exactly that purpose.

It is not for burying criticism. The starter rules deliberately keep "the last bag was
stale and shipping took nine days" and "servizio pessimo, non comprate qui": no rule
matches them, and a moderation tool has no business hiding a comment it cannot give a
reason for.

Hiding unhappy customers is also bad practice on its own terms: they escalate, screenshot,
and post again where you cannot reach it. Answer them.
