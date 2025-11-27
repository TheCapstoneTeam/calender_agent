import pytest
from scheduler_agent.email_utils import validate_emails

def test_validate_emails_valid():
    emails = ["test@gmail.com", "user@yahoo.com"]
    result = validate_emails(emails)
    assert len(result["valid"]) == 2
    assert "test@gmail.com" in result["valid"]
    assert "user@yahoo.com" in result["valid"]
    assert len(result["invalid"]) == 0
    assert len(result["typo_suggestions"]) == 0

def test_validate_emails_typo():
    emails = ["test@gmai.com"]
    result = validate_emails(emails)
    assert len(result["valid"]) == 0
    assert len(result["typo_suggestions"]) == 1
    assert result["typo_suggestions"][0]["original"] == "test@gmai.com"
    assert result["typo_suggestions"][0]["suggestion"] == "test@gmail.com"

def test_validate_emails_disposable():
    emails = ["test@mailinator.com"]
    result = validate_emails(emails)
    assert len(result["valid"]) == 0
    assert len(result["invalid"]) == 1
    assert result["invalid"][0]["email"] == "test@mailinator.com"
    assert "Disposable" in result["invalid"][0]["reason"]

def test_validate_emails_mixed():
    emails = ["valid@gmail.com", "typo@yaho.com", "junk@mailinator.com"]
    result = validate_emails(emails)
    
    assert "valid@gmail.com" in result["valid"]
    
    typos = [t["original"] for t in result["typo_suggestions"]]
    assert "typo@yaho.com" in typos
    
    invalids = [i["email"] for i in result["invalid"]]
    assert "junk@mailinator.com" in invalids
