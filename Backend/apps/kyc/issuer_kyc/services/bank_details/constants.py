
class BankDetailsConfig:
    """
    Critical fields that trigger re-verification when changed.
    Add/remove fields here without touching logic.
    """
    CRITICAL_FIELDS = [
        'account_number',
        'ifsc_code',
        'bank_name',
        'account_type',
    ]