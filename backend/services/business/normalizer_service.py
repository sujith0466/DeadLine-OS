"""
DeadlineOS Business OS — Normalization Service
==============================================
Provides deterministic normalization for monetary amounts (with Indian
numbering format support: 5k, 1.5 lakh, 2 crore), currencies, and dates.
"""

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timedelta
import zoneinfo
from utils.errors import APIError


class NormalizerService:
    @staticmethod
    def normalize_amount(raw_amount) -> str:
        """
        Deterministically parses and normalizes amount strings into a fixed 2-decimal string.
        Supports:
          - 5000, 5,000, ₹5000, Rs. 5000
          - 5k, 5K -> 5,000.00
          - 1.5 lakh, 1.5L, 1.5lakh -> 150,000.00
          - 2 crore, 2Cr, 2crore -> 20,000,000.00
        """
        if raw_amount is None:
            return "0.00"

        if isinstance(raw_amount, (int, float, Decimal)):
            return f"{Decimal(str(raw_amount)):.2f}"

        val_str = str(raw_amount).strip()
        # Remove currency symbols and formatting commas
        val_str = re.sub(r'[₹$€£\s,]', '', val_str)
        val_str = re.sub(r'^(rs\.?|inr)', '', val_str, flags=re.IGNORECASE).strip()

        # Handle 'k' / 'K' (thousands)
        k_match = re.match(r'^([\d.]+)[kK]$', val_str)
        if k_match:
            try:
                num = Decimal(k_match.group(1)) * Decimal('1000')
                return f"{num:.2f}"
            except InvalidOperation:
                pass

        # Handle 'lakh' / 'lac' / 'L' (100,000)
        lakh_match = re.match(r'^([\d.]+)(lakh|lac|L)$', val_str, flags=re.IGNORECASE)
        if lakh_match:
            try:
                num = Decimal(lakh_match.group(1)) * Decimal('100000')
                return f"{num:.2f}"
            except InvalidOperation:
                pass

        # Handle 'crore' / 'cr' (10,000,000)
        cr_match = re.match(r'^([\d.]+)(crore|cr)$', val_str, flags=re.IGNORECASE)
        if cr_match:
            try:
                num = Decimal(cr_match.group(1)) * Decimal('10000000')
                return f"{num:.2f}"
            except InvalidOperation:
                pass

        # Standard numeric string
        try:
            # Extract first continuous decimal match
            num_match = re.search(r'[-+]?\d*\.?\d+', val_str)
            if num_match:
                d = Decimal(num_match.group(0))
                return f"{d:.2f}"
        except InvalidOperation:
            pass

        return "0.00"

    @staticmethod
    def normalize_currency(raw_curr: str, default: str = 'INR') -> str:
        if not raw_curr:
            return default
        c = str(raw_curr).strip().upper()
        if c in ('₹', 'RS', 'RS.'):
            return 'INR'
        if c in ('$', 'USD'):
            return 'USD'
        if c in ('€', 'EUR'):
            return 'EUR'
        if re.match(r'^[A-Z]{3}$', c):
            return c
        return default

    @staticmethod
    def normalize_date(raw_date, tz_name: str = 'Asia/Kolkata') -> str:
        """
        Normalizes date strings to strict ISO 8601 YYYY-MM-DD.
        """
        if not raw_date:
            return date.today().isoformat()

        if isinstance(raw_date, (datetime, date)):
            return raw_date.strftime('%Y-%m-%d')

        s = str(raw_date).strip().lower()

        # Relative expressions
        today = date.today()
        if s in ('today', 'now'):
            return today.isoformat()
        if s in ('yesterday',):
            return (today - timedelta(days=1)).isoformat()
        if s in ('tomorrow',):
            return (today + timedelta(days=1)).isoformat()

        # Common date patterns
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y', '%Y/%m/%d', '%b %d, %Y'):
            try:
                dt = datetime.strptime(str(raw_date).strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass

        # Regex fallback for YYYY-MM-DD inside strings
        m = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', str(raw_date))
        if m:
            y, mo, d = m.groups()
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

        return today.isoformat()
