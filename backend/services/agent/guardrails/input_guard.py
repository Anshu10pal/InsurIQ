"""
Input guardrail — validates and sanitizes investigation queries.

Enhancements applied:
  1. PII masking        — replaces personal data with tokens, query continues
  2. Injection sanitise — strips prompt injection silently, logs attempt
  3. Auto-truncate      — long queries trimmed to last complete word, not rejected
  4. Spell correction   — common typos fixed before embedding
  5. Language detection — non-English queries translated to English
"""
import re
import logging
from typing import Tuple
from config import settings

logger = logging.getLogger(__name__)

# ── Injection patterns ────────────────────────────────────────────────────────
INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(if\s+you\s+are|a)",
    r"jailbreak",
    r"system\s*:\s*you",
    r"<\s*system\s*>",
    r"dan\s+mode",
    r"pretend\s+you\s+are",
    r"forget\s+(all\s+)?previous",
]

# ── PII patterns ──────────────────────────────────────────────────────────────
PII_PATTERNS = [
    (r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b",                          "[PERSON]"),
    (r"\b\d{3}[-.\s]\d{2}[-.\s]\d{4}\b",                       "[SSN]"),
    (r"\b\d{2}[/-]\d{2}[/-]\d{4}\b",                           "[DOB]"),
    (r"\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b",                     "[EMAIL]"),
    (r"\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b","[PHONE]"),
    (r"\b\d+\s[A-Z][a-z]+\s(Street|Road|Avenue|Drive|Lane|Close|Way)\b",
                                                                 "[ADDRESS]"),
    (r"\b(?:\d{4}[\s-]?){3}\d{4}\b",                           "[CARD]"),
    (r"\b[A-Z]{2}\d{2}\s?[A-Z]{3}\b",                          "[PLATE]"),
    (r"\b[A-Z]{2}\d{6}[A-Z]\b",                                "[PASSPORT]"),
]


def _mask_pii(query: str) -> Tuple[str, int]:
    """Replace PII with safe tokens. Returns (masked_query, count_masked)."""
    masked = query
    count = 0
    for pattern, token in PII_PATTERNS:
        matches = re.findall(pattern, masked)
        if matches:
            count += len(matches)
            masked = re.sub(pattern, token, masked)
            logger.info(f"pii_masked token={token} count={len(matches)}")
    return masked, count


def _sanitise_injection(query: str) -> Tuple[str, bool]:
    """
    Strip injection phrases silently.
    Returns (sanitised_query, injection_detected).
    """
    q = query
    detected = False
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, q.lower()):
            q = re.sub(pattern, "", q, flags=re.IGNORECASE).strip()
            detected = True
    if detected:
        logger.warning("injection_attempt_sanitised query_preview=%s", query[:60])
    return q, detected


def _auto_truncate(query: str, max_len: int) -> str:
    """
    Truncate query to last complete word within max_len.
    Never rejects — always returns a usable string.
    """
    if len(query) <= max_len:
        return query
    truncated = query[:max_len]
    last_space = truncated.rfind(" ")
    result = truncated[:last_space] if last_space > 0 else truncated
    logger.info(f"query_truncated original_len={len(query)} truncated_len={len(result)}")
    return result


def _spell_correct(query: str) -> str:
    """
    Fix common misspellings in the query.
    Falls back to original if spellchecker unavailable.
    """
    try:
        from spellchecker import SpellChecker
        spell = SpellChecker()
        words = query.split()
        corrected = []
        for word in words:
            # Only correct pure alphabetic words — skip signals, numbers, tokens
            if word.isalpha() and word.lower() not in spell:
                suggestion = spell.correction(word)
                corrected.append(suggestion if suggestion else word)
            else:
                corrected.append(word)
        result = " ".join(corrected)
        if result != query:
            logger.info("spell_correction_applied")
        return result
    except Exception:
        return query


def _translate_to_english(query: str) -> str:
    """
    Detect language and translate to English if needed.
    Falls back to original query if translation unavailable.
    """
    try:
        from langdetect import detect, LangDetectException
        try:
            lang = detect(query)
        except LangDetectException:
            return query

        if lang == "en":
            return query

        logger.info(f"non_english_query_detected lang={lang} — translating")
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source=lang, target="en").translate(query)
        logger.info("query_translated_to_english")
        return translated if translated else query
    except Exception:
        return query


def validate_input(query: str) -> Tuple[bool, str]:
    """
    Full input validation and sanitisation pipeline.

    Steps (in order):
      1. Empty check          → reject (only hard rejection)
      2. Injection sanitise   → strip silently, log, continue
      3. PII masking          → replace with tokens, continue
      4. Auto-truncate        → trim long queries, continue
      5. Too short check      → reject if still too short after cleaning
      6. Language translation → translate non-English, continue
      7. Spell correction     → fix typos, continue
      8. HTML char strip      → remove <>"' characters
    """
    # 1. Empty check — only true hard rejection
    if not query or not query.strip():
        return False, "Query cannot be empty"

    q = query.strip()

    # 2. Injection sanitise — strip silently, never reject
    q, _ = _sanitise_injection(q)

    # 3. PII masking — replace with tokens, never reject
    q, pii_count = _mask_pii(q)
    if pii_count > 0:
        logger.info(f"pii_fields_masked total={pii_count}")

    # 4. Auto-truncate — trim long queries instead of rejecting
    q = _auto_truncate(q, settings.max_query_length)

    # 5. Too short — only reject after all cleaning is done
    if len(q) < settings.min_query_length:
        return False, f"Query too short (minimum {settings.min_query_length} characters)"

    # 6. Language translation — translate non-English to English
    q = _translate_to_english(q)

    # 7. Spell correction — fix typos before embedding
    q = _spell_correct(q)

    # 8. Strip HTML chars
    q = re.sub(r'[<>"\']', '', q).strip()

    return True, q


def is_insurance_relevant(query: str) -> bool:
    insurance_keywords = [
        "claim", "fraud", "policy", "vehicle", "accident", "insurance",
        "agent", "repair", "supplement", "witness", "police", "collision",
        "liability", "deductible", "claimant", "suspicious", "investigate",
    ]
    q_lower = query.lower()
    return any(kw in q_lower for kw in insurance_keywords)