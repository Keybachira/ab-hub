"""Security analyzer unit tests."""

from ab_hub.analyzers.security import security_score, normalize_ecosystem


def test_normalize_ecosystem():
    assert normalize_ecosystem("npm") == "npm"
    assert normalize_ecosystem("pypi") == "PyPI"
    assert normalize_ecosystem("PyPI") == "PyPI"
    assert normalize_ecosystem("unknown-eco") is None


def test_security_score_clean():
    result = security_score([])
    assert result["status"] == "Clean"
    assert result["health_score"] == 100
    assert result["total"] == 0


def test_security_score_critical():
    findings = [
        {"severity": "CRITICAL"},
        {"severity": "HIGH"},
        {"severity": "LOW"},
    ]
    result = security_score(findings)
    assert result["status"] == "Critical"
    assert result["counts"]["CRITICAL"] == 1
    assert result["counts"]["HIGH"] == 1
    assert result["health_score"] < 100
