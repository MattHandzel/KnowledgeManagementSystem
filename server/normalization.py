import re


def to_kebab_case(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[_\s]+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.lower().strip("-")


def singularize_tag(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    lower = s.lower()
    if lower.endswith("ies") and len(lower) > 3:
        return lower[:-3] + "y"
    if lower.endswith("ses") and len(lower) > 3:
        return lower[:-2]
    if lower.endswith("s") and not lower.endswith("ss"):
        return lower[:-1]
    return lower


def dedupe_preserve_order(values):
    seen = set()
    out = []
    for v in values:
        k = v.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(v)
    return out
