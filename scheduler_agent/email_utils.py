import difflib
from typing import List, Dict, Any
from email_validator import validate_email, EmailNotValidError
from disposable_email_domains import blocklist

# Common email domains for typo checking
COMMON_DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", 
    "icloud.com", "aol.com", "protonmail.com", "zoho.com"
]

def validate_emails(emails: List[str]) -> Dict[str, Any]:
    """
    Validates a list of email addresses.

    Checks for:
    1. Syntax and deliverability (DNS check)
    2. Disposable email domains
    3. Common domain typos (e.g. gmai.com -> gmail.com)

    Args:
        emails: List of email address strings.

    Returns:
        Dictionary with:
        - "valid": List of valid email strings.
        - "invalid": List of dictionaries with "email" and "reason".
        - "typo_suggestions": List of dictionaries with "original", "suggestion".
    """
    valid_emails = []
    invalid_emails = []
    typo_suggestions = []

    for email in emails:
        email = email.strip()
        if not email:
            continue

        # 1. Check for typos in the domain first (heuristic)
        try:
            local_part, domain = email.split('@')
            # Find close matches to common domains
            matches = difflib.get_close_matches(domain, COMMON_DOMAINS, n=1, cutoff=0.85)
            if matches and matches[0] != domain:
                suggestion = f"{local_part}@{matches[0]}"
                typo_suggestions.append({
                    "original": email,
                    "suggestion": suggestion
                })
                # We treat it as invalid/pending confirmation if there's a likely typo
                continue 
        except ValueError:
            # Split failed, likely invalid format, let email-validator handle it
            pass

        # 2. Check if it's a known disposable domain
        try:
            _, domain_part = email.split('@')
            if domain_part in blocklist:
                invalid_emails.append({
                    "email": email,
                    "reason": "Disposable email addresses are not allowed."
                })
                continue
        except ValueError:
            pass # Let validator handle malformed emails

        # 3. Validate syntax and deliverability
        try:
            # check_deliverability=True queries DNS
            v = validate_email(email, check_deliverability=True)
            valid_emails.append(v.normalized) # Use normalized form
        except EmailNotValidError as e:
            invalid_emails.append({
                "email": email,
                "reason": str(e)
            })

    return {
        "valid": valid_emails,
        "invalid": invalid_emails,
        "typo_suggestions": typo_suggestions
    }
