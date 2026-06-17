"""
Security utilities for the Log Analyzer.
"""

import re
from typing import List


class PIIMasker:
    """
    Utility class to detect and mask Personally Identifiable Information (PII)
    before sending data to external AI providers or logging it.
    """

    # Common regex patterns for PII
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    PHONE_PATTERN = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
    CREDIT_CARD_PATTERN = r"\b(?:\d[ -]*?){13,16}\b"

    @staticmethod
    def mask_pii(text: str) -> str:
        """
        Masks common PII in the given string.

        Args:
            text (str): The raw log or user input string.

        Returns:
            str: The sanitized string with PII replaced by placeholders.
        """
        if not text:
            return text

        text = re.sub(PIIMasker.EMAIL_PATTERN, "[EMAIL_REDACTED]", text)
        text = re.sub(PIIMasker.PHONE_PATTERN, "[PHONE_REDACTED]", text)
        # Prevent masking standard trace IDs that might look like cards
        # (This is a simplified example. In production log systems, CC patterns need Luhn checks).
        text = re.sub(PIIMasker.CREDIT_CARD_PATTERN, "[CC_REDACTED]", text)

        return text
