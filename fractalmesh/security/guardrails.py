from __future__ import annotations

import re


class Guardrails:
    EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    CARD_RE = re.compile(r"\b(?:\d[ -]?){13,16}\b")
    PHONE_RE = re.compile(
        r"\b(?:\+?1[ .-]?)?(?:\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4})\b"
    )
    INJECTION_PATTERNS = [
        re.compile(r"(;|&&|\|\||`|\$\()"),
        re.compile(r"\b(?:rm\s+-rf|curl\s+https?://|wget\s+https?://)\b", re.I),
        re.compile(r"\b(?:bash|sh|powershell)\s+-c\b", re.I),
    ]

    def redact_pii(self, text: str) -> str:
        redacted = self.EMAIL_RE.sub("[REDACTED_EMAIL]", text)
        redacted = self.SSN_RE.sub("[REDACTED_SSN]", redacted)
        redacted = self.CARD_RE.sub("[REDACTED_CARD]", redacted)
        redacted = self.PHONE_RE.sub("[REDACTED_PHONE]", redacted)
        return redacted

    def check_injection(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in self.INJECTION_PATTERNS)

    def filter_input(self, text: str) -> str:
        redacted = self.redact_pii(text)
        if self.check_injection(redacted):
            raise ValueError("Potential command injection detected")
        return redacted

    def filter_output(self, text: str) -> str:
        return self.redact_pii(text)
