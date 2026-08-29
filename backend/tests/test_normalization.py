"""
B2 Test Suite — Deterministic Normalization
===========================================
Tests Indian numbering format normalizer (5k, 1.5 lakh, 2 crore) and ISO dates.
"""

from services.business.normalizer_service import NormalizerService


def test_amount_normalization_indian_formats():
    assert NormalizerService.normalize_amount("5000") == "5000.00"
    assert NormalizerService.normalize_amount("5,000") == "5000.00"
    assert NormalizerService.normalize_amount("₹5,000.50") == "5000.50"
    assert NormalizerService.normalize_amount("5k") == "5000.00"
    assert NormalizerService.normalize_amount("12.5K") == "12500.00"
    assert NormalizerService.normalize_amount("1.5 lakh") == "150000.00"
    assert NormalizerService.normalize_amount("1.5L") == "150000.00"
    assert NormalizerService.normalize_amount("2 crore") == "20000000.00"
    assert NormalizerService.normalize_amount("2Cr") == "20000000.00"


def test_currency_and_date_normalization():
    assert NormalizerService.normalize_currency("₹") == "INR"
    assert NormalizerService.normalize_currency("rs.") == "INR"
    assert NormalizerService.normalize_currency("USD") == "USD"

    assert NormalizerService.normalize_date("2026-08-29") == "2026-08-29"
    assert NormalizerService.normalize_date("29/08/2026") == "2026-08-29"
    assert NormalizerService.normalize_date("29 Aug 2026") == "2026-08-29"
