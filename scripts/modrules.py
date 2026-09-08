#!/usr/bin/env python3
"""modrules - a comment moderation rule engine you can read the verdicts of.

Most "hide Facebook comments" scripts hide everything new. That buries genuine
questions and honest criticism along with the spam, which is why the category has the
reputation it has. This decides, records which rule decided, and says why.

  modrules.py test    "buy now at crypto-x(dot)com"
  modrules.py test    comments.csv --rules rules.json
  modrules.py rules   --starter > rules.json
  modrules.py explain "check my profile" --rules rules.json

Pure standard library, Python 3.8+. No network, no dependencies. Nothing here talks to
any platform: it decides, you deliver the decision.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata

# --------------------------------------------------------------------------
# text normalisation
# --------------------------------------------------------------------------

def fold(text):
    """Lowercase and strip accents, so `perche` matches `PERCHÈ`."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


EMOJI_RANGES = (
    (0x1F300, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF),
    (0x1F1E6, 0x1F1FF), (0xFE0F, 0xFE0F), (0x2190, 0x21FF),
)


def count_emoji(text):
    n = 0
    for ch in text or "":
        cp = ord(ch)
        if any(lo <= cp <= hi for lo, hi in EMOJI_RANGES):
            n += 1
    return n


# --------------------------------------------------------------------------
# matchers, one per rule kind
# --------------------------------------------------------------------------

URL_RE = re.compile(
    r"(https?://\S+"
    r"|www\.\S+"
    r"|\b[\w-]+\.(com|net|org|io|co|xyz|shop|store|info|biz|ru|cn|top|club|online|site)\b)",
    re.IGNORECASE)

# example(dot)com, example dot com, example[.]com, example . com
OBFUSCATED_RE = re.compile(
    r"\b[\w-]{2,}\s*(?:\(|\[|\{)?\s*(?:dot|punto|point|\.)\s*(?:\)|\]|\})?\s*"
    r"(com|net|org|io|co|xyz|shop|store|info|biz|ru|cn|top|club|online|site)\b",
    re.IGNORECASE)

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
HANDLE_RE = re.compile(r"(?<![\w.])@[A-Za-z0-9._]{3,}")
PHONE_RE = re.compile(r"(?:\+|00)?\d[\d\s().-]{7,}\d")


def match_keyword(comment, pattern):
    """Whole-word, case and accent insensitive. Comma-separated terms."""
    text = fold(comment)
    for term in (t.strip() for t in pattern.split(",")):
        if not term:
            continue
        folded = fold(term)
        if re.search(r"(?<!\w)%s(?!\w)" % re.escape(folded), text):
            return "matched the term %r" % term
    return None


def match_regex(comment, pattern):
    """An invalid expression is skipped, never fatal. One bad rule must not stop
    moderation on every other comment."""
    try:
        compiled = re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None
    m = compiled.search(comment or "")
    return "matched the expression at %r" % m.group(0)[:40] if m else None


def match_link(comment, _pattern):
    m = URL_RE.search(comment or "")
    if m:
        return "contains a link: %r" % m.group(0)[:40]
    m = OBFUSCATED_RE.search(comment or "")
    if m:
        return "contains an obfuscated link: %r" % m.group(0)[:40]
    return None


def match_contact(comment, _pattern):
    text = comment or ""
    m = EMAIL_RE.search(text)
    if m:
        return "contains an email address"
    m = HANDLE_RE.search(text)
    if m:
        return "contains the handle %r" % m.group(0)[:24]
    m = PHONE_RE.search(text)
    if m and len(re.sub(r"\D", "", m.group(0))) >= 8:
        return "contains a phone number"
    return None


def match_emoji_spam(comment, pattern):
    try:
        threshold = int(pattern)
    except (TypeError, ValueError):
        threshold = 5
    n = count_emoji(comment)
    return "carries %d emoji, threshold %d" % (n, threshold) if n >= threshold else None


def match_min_length(comment, pattern):
    try:
        threshold = int(pattern)
    except (TypeError, ValueError):
        threshold = 3
    length = len((comment or "").strip())
    return "is %d characters, minimum %d" % (length, threshold) if length < threshold else None


def match_author_allow(comment, pattern, author=None):
    if not author:
        return None
    folded = fold(author)
    for name in (n.strip() for n in pattern.split(",")):
        if name and fold(name) == folded:
            return "author %r is on the allow list" % author
    return None


MATCHERS = {
    "keyword": match_keyword,
    "regex": match_regex,
    "link": match_link,
    "contact": match_contact,
    "emoji_spam": match_emoji_spam,
    "min_length": match_min_length,
    "author_allow": match_author_allow,
}

# --------------------------------------------------------------------------
# the engine
# --------------------------------------------------------------------------

SPAM_KEYWORDS = ",".join([
    "whatsapp me", "dm me", "inbox me", "write me on", "contact me on",
    "investment", "forex signals", "binary options", "crypto expert",
    "recover your lost", "hacked account", "bitcoin mining",
    "click the link in my bio", "check my profile", "follow for follow",
    "cheap followers", "buy followers", "free giveaway click",
    "make money fast", "earn from home guaranteed", "no risk guaranteed",
])

STARTER_RULES = [
    {"kind": "author_allow", "pattern": "", "action": "allow",
     "label": "Team and known customers", "priority": 1, "enabled": False},
    {"kind": "link", "pattern": "", "action": "hide",
     "label": "Links", "priority": 10, "enabled": True},
    {"kind": "contact", "pattern": "", "action": "hide",
     "label": "Contact details", "priority": 20, "enabled": True},
    {"kind": "keyword", "pattern": SPAM_KEYWORDS, "action": "hide",
     "label": "Known spam and scam phrases", "priority": 30, "enabled": True},
    {"kind": "emoji_spam", "pattern": "6", "action": "hide",
     "label": "Emoji flooding", "priority": 40, "enabled": True},
    {"kind": "min_length", "pattern": "2", "action": "hide",
     "label": "Empty or single-character comments", "priority": 50, "enabled": True},
]


def evaluate(comment, rules, author=None):
    """Allow rules run FIRST, always, then the rest in priority order, first match wins.

    Ordering allow rules first is the whole safety property: an allow list that could be
    outranked by a higher-priority hide rule is not an allow list.
    """
    active = [r for r in rules if r.get("enabled", True)]
    allows = sorted((r for r in active if r.get("action") == "allow"),
                    key=lambda r: r.get("priority", 100))
    others = sorted((r for r in active if r.get("action") != "allow"),
                    key=lambda r: r.get("priority", 100))

    evaluated = []
    for rule in allows + others:
        matcher = MATCHERS.get(rule["kind"])
        if matcher is None:
            evaluated.append({"rule": rule.get("label") or rule["kind"],
                              "matched": False, "reason": "unknown rule kind"})
            continue
        if rule["kind"] == "author_allow":
            reason = matcher(comment, rule.get("pattern", ""), author)
        else:
            reason = matcher(comment, rule.get("pattern", ""))
        evaluated.append({"rule": rule.get("label") or rule["kind"],
                          "matched": reason is not None, "reason": reason})
        if reason is not None:
            return {
                "verdict": rule.get("action", "hide"),
                "rule": rule.get("label") or rule["kind"],
                "kind": rule["kind"],
                "reason": reason,
                "evaluated": evaluated,
            }
    return {"verdict": "keep", "rule": None, "kind": None,
            "reason": "no rule matched", "evaluated": evaluated}


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def load_rules(path):
    if not path:
        return STARTER_RULES
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


VERDICT_LABEL = {"hide": "WOULD HIDE", "flag": "WOULD FLAG",
                 "allow": "WOULD KEEP (allowed)", "keep": "WOULD KEEP"}


def cmd_test(args):
    rules = load_rules(args.rules)
    rows = []
    if args.source.lower().endswith(".csv"):
        with open(args.source, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                rows.append((r.get("message") or r.get("comment") or "",
                             r.get("author") or r.get("from") or ""))
    else:
        rows.append((args.source, args.author or ""))

    results = []
    for message, author in rows:
        v = evaluate(message, rules, author)
        results.append({"comment": message, "author": author, **v})

    if args.json:
        print(json.dumps([{k: r[k] for k in
                           ("comment", "author", "verdict", "rule", "reason")}
                          for r in results], indent=2, ensure_ascii=False))
        return 0

    for r in results:
        print("%-22s %s" % (VERDICT_LABEL[r["verdict"]], r["comment"][:62]))
        if r["rule"]:
            print("%-22s %s: %s" % ("", r["rule"], r["reason"]))
    hidden = sum(1 for r in results if r["verdict"] == "hide")
    kept = sum(1 for r in results if r["verdict"] in ("keep", "allow"))
    if len(results) > 1:
        print("\n%d comment(s): %d would be hidden, %d kept" % (len(results), hidden, kept))
        print("This is a dry run. Nothing was sent anywhere.")
    return 0


def cmd_rules(args):
    print(json.dumps(STARTER_RULES, indent=2, ensure_ascii=False))
    return 0


def cmd_explain(args):
    rules = load_rules(args.rules)
    v = evaluate(args.comment, rules, args.author)
    print("comment   %s" % args.comment)
    print("verdict   %s" % VERDICT_LABEL[v["verdict"]])
    print("reason    %s\n" % v["reason"])
    print("rules evaluated, in the order they ran:")
    for e in v["evaluated"]:
        mark = "MATCH" if e["matched"] else "  -  "
        print("  %s %-38s %s" % (mark, e["rule"], e["reason"] or ""))
    if v["verdict"] == "keep":
        print("\nNo rule matched, so this comment stays visible. A moderation tool has no")
        print("business hiding a comment it cannot give a reason for.")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="modrules", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")

    t = sub.add_parser("test", help="dry run one comment or a CSV of them")
    t.add_argument("source", help="a comment, or a .csv with a message column")
    t.add_argument("--author")
    t.add_argument("--rules", help="rules JSON; omit for the starter set")
    t.add_argument("--json", action="store_true")
    t.set_defaults(func=cmd_test)

    r = sub.add_parser("rules", help="print the starter rule set")
    r.add_argument("--starter", action="store_true")
    r.set_defaults(func=cmd_rules)

    e = sub.add_parser("explain", help="show every rule that ran and why it did not match")
    e.add_argument("comment")
    e.add_argument("--author")
    e.add_argument("--rules")
    e.set_defaults(func=cmd_explain)

    args = p.parse_args(argv)
    if not getattr(args, "func", None):
        p.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
