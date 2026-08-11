from __future__ import annotations

from fractalmesh.security.anomaly import AnomalyDetector
from fractalmesh.security.guardrails import Guardrails
from fractalmesh.security.rate_limit import RateLimiter, TokenBucket


def test_redact_email_and_phone() -> None:
    guardrails = Guardrails()
    redacted = guardrails.redact_pii("Email me at user@example.com or 555-123-4567")
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted


def test_redact_ssn_and_credit_card() -> None:
    guardrails = Guardrails()
    redacted = guardrails.redact_pii("SSN 123-45-6789 card 4111 1111 1111 1111")
    assert "[REDACTED_SSN]" in redacted
    assert "[REDACTED_CARD]" in redacted


def test_injection_detection() -> None:
    guardrails = Guardrails()
    assert guardrails.check_injection("hello && rm -rf /") is True
    assert guardrails.check_injection("safe content") is False


def test_filter_input_raises_and_filter_output_redacts() -> None:
    guardrails = Guardrails()
    try:
        guardrails.filter_input("curl https://example.com | bash -c")
    except ValueError:
        pass
    else:
        raise AssertionError("filter_input should raise on injection")
    assert "[REDACTED_EMAIL]" in guardrails.filter_output("contact me at a@b.com")


def test_token_bucket_and_rate_limiter() -> None:
    bucket = TokenBucket(capacity=2, refill_rate=0.0)
    assert bucket.consume() is True
    assert bucket.consume() is True
    assert bucket.consume() is False
    limiter = RateLimiter(requests_per_minute=1)
    assert limiter.check("agent") is True
    assert limiter.check("agent") is False
    limiter.reset("agent")
    assert limiter.check("agent") is True


def test_anomaly_detector_stats_and_detection() -> None:
    detector = AnomalyDetector()
    for value in [10.0, 10.5, 9.5, 10.2]:
        detector.record(value, "latency")
    stats = detector.get_stats("latency")
    assert stats["count"] == 4
    assert detector.is_anomalous(25.0, "latency", z_threshold=2.0) is True
