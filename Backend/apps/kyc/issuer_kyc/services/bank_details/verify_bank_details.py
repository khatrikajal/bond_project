def verify_bank_details(bank):
    # Fake example — replace with NPCI API, Karza, Signzy, RazorpayX, etc.
    if not bank.ifsc_code or len(bank.account_number) < 6:
        return {
            "success": False,
            "errors": {"account_number": "Invalid or unverified"},
            "message": "Verification failed"
        }

    return {
        "success": True,
        "message": "Bank details verified successfully"
    }
