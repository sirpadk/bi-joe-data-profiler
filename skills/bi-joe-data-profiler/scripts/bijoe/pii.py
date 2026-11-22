"""Personal data: spot it, mask it, and check that none of it leaked into the wiki.

The engine reads raw values in memory only. Anything it writes (profile.json, the wiki, the
evidence the agent reads) has the values of personal data columns removed, so neither the agent
nor the reader ever sees them. Counts, missing values, distinct counts and lengths are not
personal and stay.

Detection is a heuristic, so it works in two ways: column names (English and Danish) and the
shape of the values. A column the engine misses can be forced with `--mask Table.Column`, and
`bijoe check` scans the finished wiki for patterns that look like personal data.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

MASK = "••••"
SAMPLE_VALUES = 200  # distinct values looked at when judging by the shape of the values
MIN_VALUES = 3
SHARE = 0.8  # this share of the values must look alike

#: column-name hints. A name matches when it contains the hint (letters and digits only, lower case).
NAME_HINTS: Dict[str, Tuple[str, ...]] = {
    "national id": ("ssn", "socialsecurity", "cpr", "personnummer", "nationalid", "nationalidentity", "taxid",
                    "passport", "driverlicense", "driverslicense"),
    "email": ("email", "epost"),
    "phone": ("phone", "telephone", "mobile", "telefon", "tlf", "fax", "mobil"),
    "person name": ("firstname", "lastname", "surname", "middlename", "fullname", "givenname", "familyname",
                    "forename", "fornavn", "efternavn", "customername", "employeename", "personname",
                    "contactname", "patientname", "membername", "username", "manager"),
    "address": ("street", "address", "adresse", "housenumber", "streetname"),
    "birth date": ("birth", "dob", "foedsel"),
    "bank or card number": ("iban", "bankaccount", "kontonummer", "creditcard", "cardnumber", "ccnumber"),
    "ip address": ("ipaddress",),
    "credential": ("password", "passwd", "passwordhash", "passwordsalt", "apikey", "secretkey", "clientsecret"),
}
_ID_ENDINGS = ("id", "key", "ref", "code", "flag", "optin", "consent")

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_EMAIL_ANY = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_US_SSN = re.compile(r"^\d{3}-\d{2}-\d{4}$")
_US_SSN_ANY = re.compile(r"(?<![\d-])\d{3}-\d{2}-\d{4}(?![\d-])")
_CPR = re.compile(r"^(\d{2})(\d{2})(\d{2})-?(\d{4})$")
_CPR_DASHED_ANY = re.compile(r"(?<![\d-])(\d{2})(\d{2})(\d{2})-(\d{4})(?![\d-])")
_IBAN = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$")
_IBAN_ANY = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,7}(?: ?[A-Z0-9]{1,4})?\b")
_CARD = re.compile(r"^\d{13,19}$")
_CARD_ANY = re.compile(r"(?<![\d-])(?:\d[ -]?){13,19}(?![\d-])")
_IP = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_PHONE = re.compile(r"^(?:\+\d{1,3}[\s-]?)?(?:\(\d{2,4}\)[\s-]?)?\d{2,4}[\s.-]\d{2,4}(?:[\s.-]\d{2,4})*$")


def _norm(name: str) -> str:
    low = name.lower().replace("æ", "ae").replace("ø", "oe").replace("å", "aa")
    return re.sub(r"[^a-z0-9]", "", low)


def _luhn(digits: str) -> bool:
    total, flip = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if flip:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
        flip = not flip
    return total % 10 == 0


def _valid_cpr(m: "re.Match[str]") -> bool:
    day, month = int(m.group(1)), int(m.group(2))
    return 1 <= day <= 31 and 1 <= month <= 12


def _looks_like(kind: str, value: str) -> bool:
    if kind == "email":
        return bool(_EMAIL.match(value))
    if kind == "national id":
        if _US_SSN.match(value):
            return True
        m = _CPR.match(value)
        return bool(m) and _valid_cpr(m) and "-" in value  # plain digits are too common to call personal
    if kind == "bank or card number":
        flat = value.replace(" ", "").replace("-", "")
        return bool(_IBAN.match(flat)) or (bool(_CARD.match(flat)) and _luhn(flat))
    if kind == "ip address":
        return bool(_IP.match(value)) and all(int(p) <= 255 for p in value.split("."))
    if kind == "phone":
        digits = re.sub(r"\D", "", value)
        return bool(_PHONE.match(value)) and 8 <= len(digits) <= 15
    return False


def classify(name: str, inferred_type: str, values: Iterable[str]) -> Optional[Dict[str, str]]:
    """Return {"class": ..., "reason": ...} when the column looks like personal data, else None."""
    if inferred_type in ("boolean", "binary", "empty"):
        return None
    norm = _norm(name)
    try:
        few = inferred_type in ("integer", "decimal") and len(values) <= 20  # a flag or a code, not a person's number
    except TypeError:
        few = False
    if few:
        return None
    ids = norm.endswith(_ID_ENDINGS)
    if not ids:
        for kind, hints in NAME_HINTS.items():
            if any(h in norm for h in hints):
                if kind == "birth date" and inferred_type not in ("date", "datetime"):
                    continue
                if kind != "birth date" and inferred_type in ("date", "datetime", "decimal"):
                    continue
                return {"class": kind, "reason": "the column name"}
    if inferred_type in ("text", "integer"):
        sample = [v for v in itertools.islice(values, SAMPLE_VALUES) if v]
        if len(sample) >= MIN_VALUES:
            for kind in ("email", "national id", "bank or card number", "ip address", "phone"):
                if sum(_looks_like(kind, v) for v in sample) >= SHARE * len(sample):
                    return {"class": kind, "reason": "the shape of the values"}
    return None


def parse_forced(spec: Optional[str]) -> List[Tuple[str, str]]:
    """'Customers.Email, Stores.Manager' -> [('customers', 'email'), ...]"""
    out = []
    for part in (spec or "").split(","):
        part = part.strip()
        if "." in part:
            table, column = part.rsplit(".", 1)
            out.append((table.strip().lower(), column.strip().lower()))
    return out


# ---- a safety net for the finished wiki --------------------------------------------------

def scan_text(text: str) -> List[str]:
    """Kinds of personal data that still appear in a piece of text (empty list when it looks clean)."""
    found = []
    if _EMAIL_ANY.search(text):
        found.append("an email address")
    if _US_SSN_ANY.search(text) or any(_valid_cpr(m) for m in _CPR_DASHED_ANY.finditer(text)):
        found.append("a national ID number")
    if _IBAN_ANY.search(text):
        found.append("an IBAN-like bank account number")
    for m in _CARD_ANY.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn(digits):
            found.append("a card number")
            break
    return found


def scan_wiki(out_dir: Path) -> List[Tuple[str, str]]:
    """(file, what) for every page or JSON file in the wiki that still holds something personal."""
    hits = []
    for path in sorted(out_dir.rglob("*")):
        if path.suffix not in (".md", ".json") or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for what in scan_text(text):
            hits.append((str(path.relative_to(out_dir)), what))
    return hits
