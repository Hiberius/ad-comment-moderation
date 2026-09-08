#!/usr/bin/env python3
"""Zero-dependency test suite. Run: python3 tests/test_modrules.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import modrules as M  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILED.append(name)


def verdict(comment, rules=None, author=None):
    return M.evaluate(comment, rules or M.STARTER_RULES, author)["verdict"]


print("normalisation")
check("accents folded", M.fold("PERCHÈ") == "perche")
check("case folded", M.fold("CIAO") == "ciao")
check("emoji counted", M.count_emoji("ciao 🔥🔥🔥") == 3)
check("plain text has no emoji", M.count_emoji("ciao") == 0)

print("keyword")
check("whole word match", M.match_keyword("please dm me now", "dm me") is not None)
check("accent insensitive", M.match_keyword("PERCHÈ no", "perche") is not None)
check("substring alone does not match",
      M.match_keyword("dming is fine", "dm") is None)
check("empty terms are skipped", M.match_keyword("hello", ",,") is None)

print("links")
for text in ("visit https://spam.example", "www.spam.example", "go to spam.xyz",
             "crypto-x(dot)com", "example [.] com", "example dot com"):
    check("link found in %r" % text[:28], M.match_link(text, "") is not None)
check("a sentence with a full stop is not a link",
      M.match_link("Bello. Grazie mille.", "") is None)
check("a decimal number is not a link", M.match_link("costa 12.50 euro", "") is None)

print("contact details")
check("email found", M.match_contact("write to a@b.com", "") is not None)
check("handle found", M.match_contact("scrivi a @spammer99", "") is not None)
check("phone found", M.match_contact("chiama +39 333 1234567", "") is not None)
check("a short number is not a phone", M.match_contact("costa 12 euro", "") is None)
check("plain text has no contact", M.match_contact("bel prodotto", "") is None)

print("emoji flooding and length")
check("seven emoji trips a threshold of six",
      M.match_emoji_spam("🔥🔥🔥🔥🔥🔥🔥", "6") is not None)
check("three emoji do not", M.match_emoji_spam("🔥🔥🔥", "6") is None)
check("a bad threshold falls back to five",
      M.match_emoji_spam("🔥🔥🔥🔥🔥", "not a number") is not None)
check("a single character is too short", M.match_min_length(".", "2") is not None)
check("a real sentence is long enough", M.match_min_length("ciao", "2") is None)

print("regex")
check("a valid expression matches", M.match_regex("codice ABC123", r"[A-Z]{3}\d{3}") is not None)
check("an invalid expression is skipped, never fatal",
      M.match_regex("anything", "([unclosed") is None)

print("the safety property: allow rules run first")
rules = [
    {"kind": "link", "pattern": "", "action": "hide", "priority": 1, "label": "Links"},
    {"kind": "author_allow", "pattern": "Marco Rossi", "action": "allow",
     "priority": 99, "label": "Team"},
]
check("a lower-priority allow still beats a higher-priority hide",
      verdict("guarda su example.com", rules, author="Marco Rossi") == "allow")
check("the same comment from anyone else is hidden",
      verdict("guarda su example.com", rules, author="Someone Else") == "hide")

print("priority and first match wins")
rules = [
    {"kind": "keyword", "pattern": "sconto", "action": "flag", "priority": 5,
     "label": "Watch"},
    {"kind": "keyword", "pattern": "sconto", "action": "hide", "priority": 10,
     "label": "Hide"},
]
r = M.evaluate("che sconto avete?", rules)
check("the lower priority number wins", r["verdict"] == "flag" and r["rule"] == "Watch")
disabled = [dict(rules[0], enabled=False), dict(rules[1], enabled=True)]
check("a disabled rule is skipped", M.evaluate("sconto", disabled)["verdict"] == "hide")

print("the starter set on real comments")
check("obfuscated link spam is hidden",
      verdict("Buy cheap followers at crypto-x(dot)com now") == "hide")
check("follower farming is hidden", verdict("check my profile") == "hide")
check("emoji flood is hidden", verdict("🔥🔥🔥🔥🔥🔥🔥") == "hide")
check("a phone number is hidden", verdict("Chiamami al +39 333 1234567") == "hide")
check("an empty comment is hidden", verdict(".") == "hide")

print("the property that matters: criticism survives")
for complaint in [
    "Honestly the last bag was stale and shipping took nine days. Disappointed.",
    "Servizio PESSIMO non comprate qui",
    "Ho aspettato tre settimane e nessuno mi ha risposto",
    "This is overpriced for what it is",
    "Il prodotto non corrisponde alla descrizione",
]:
    check("kept: %r" % complaint[:38], verdict(complaint) == "keep")
check("an ordinary question is kept",
      verdict("Quanto costa la spedizione in Sicilia?") == "keep")

print("verdicts are explainable")
r = M.evaluate("crypto-x(dot)com", M.STARTER_RULES)
check("the deciding rule is named", r["rule"] == "Links")
check("a human-readable reason is given", "obfuscated link" in r["reason"])
check("every rule that ran is listed", len(r["evaluated"]) >= 1)
r = M.evaluate("bel prodotto grazie", M.STARTER_RULES)
check("a kept comment lists every rule that did not match",
      len(r["evaluated"]) == len([x for x in M.STARTER_RULES if x.get("enabled", True)]))
check("a kept comment says so plainly", r["reason"] == "no rule matched")

print("")
if FAILED:
    print("%d test(s) failed: %s" % (len(FAILED), ", ".join(FAILED)))
    sys.exit(1)
print("all tests passed")
