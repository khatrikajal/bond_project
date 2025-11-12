from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from ..model.borrowing_details import BorrowingType, RepaymentTerms


def calculate_monthly_interest(principal: Decimal, annual_rate: Decimal) -> Decimal:
    """
    Calculate the monthly interest payment from principal and annual interest rate.

    Formula:
        monthly_interest = (principal * annual_rate / 100) / 12

    Returns:
        Decimal: monthly interest amount (rounded to 2 decimal places)
    """
    try:
        if not principal or not annual_rate:
            return Decimal('0.00')

        monthly_interest = (Decimal(principal) * Decimal(annual_rate) / Decimal('100')) / Decimal('12')
        return monthly_interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ZeroDivisionError):
        return Decimal('0.00')


def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
    """
    Calculate the EMI (Equated Monthly Installment) for a loan.

    Formula:
        EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    where:
        P = Principal
        r = Monthly interest rate (annual_rate / 12 / 100)
        n = Number of months

    Returns:
        Decimal: EMI amount (rounded to 2 decimal places)
    """
    try:
        principal = Decimal(principal)
        annual_rate = Decimal(annual_rate)
        tenure_months = int(tenure_months)

        if principal <= 0 or tenure_months <= 0:
            return Decimal('0.00')

        monthly_rate = annual_rate / Decimal('1200')  # annual_rate / 12 / 100

        if monthly_rate == 0:
            emi = principal / tenure_months
        else:
            factor = (1 + monthly_rate) ** tenure_months
            emi = (principal * monthly_rate * factor) / (factor - 1)

        return emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ZeroDivisionError, ValueError):
        return Decimal('0.00')


def validate_borrowing_data(data: dict):
    """
    Validate borrowing data for correctness and completeness.

    Returns:
        tuple: (is_valid: bool, errors: list of error messages)

    Validations:
    - All required fields must be present
    - Numeric fields (amounts, percentages) must be positive
    - BorrowingType and RepaymentTerms must match defined enum choices
    """
    errors = []

    # Required fields
    required_fields = ['company_id', 'lender_name', 'lender_amount', 'borrowing_type', 'repayment_terms']
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            errors.append(f"{field} is required.")

    # Validate lender amount
    try:
        lender_amount = Decimal(str(data.get('lender_amount', '0')))
        if lender_amount <= 0:
            errors.append("Lender amount must be greater than 0.")
    except InvalidOperation:
        errors.append("Invalid lender amount format.")

    # Validate monthly payments (if present)
    for key in ['monthly_principal_payment', 'monthly_interest_payment', 'interest_payment_percentage']:
        if key in data and data[key] not in [None, ""]:
            try:
                val = Decimal(str(data[key]))
                if val < 0:
                    errors.append(f"{key} cannot be negative.")
                if key == 'interest_payment_percentage' and val > 100:
                    errors.append("Interest percentage cannot exceed 100%.")
            except InvalidOperation:
                errors.append(f"Invalid numeric value for {key}.")

    # Validate borrowing_type against enum
    borrowing_type = data.get('borrowing_type')
    valid_borrowing_types = [choice[0] for choice in BorrowingType.choices]
    if borrowing_type and borrowing_type not in valid_borrowing_types:
        errors.append(
            f"Invalid borrowing_type '{borrowing_type}'. "
            f"Valid options are: {', '.join(valid_borrowing_types)}."
        )

    # Validate repayment_terms against enum
    repayment_terms = data.get('repayment_terms')
    valid_repayment_terms = [choice[0] for choice in RepaymentTerms.choices]
    if repayment_terms and repayment_terms not in valid_repayment_terms:
        errors.append(
            f"Invalid repayment_terms '{repayment_terms}'. "
            f"Valid options are: {', '.join(valid_repayment_terms)}."
        )

    return (len(errors) == 0, errors)


def calculate_borrowing_summary(borrowings):
    """
    Calculate aggregated borrowing summary for analytics.

    Args:
        borrowings (QuerySet or list of BorrowingDetails)

    Returns:
        dict: summary data including totals and averages.
    """
    total_borrowings = len(borrowings)
    total_amount = Decimal('0.00')
    total_principal = Decimal('0.00')
    total_interest = Decimal('0.00')
    weighted_interest_sum = Decimal('0.00')

    by_type = {choice[0]: {'count': 0, 'amount': Decimal('0.00')} for choice in BorrowingType.choices}

    for b in borrowings:
        total_amount += b.lender_amount
        total_principal += b.monthly_principal_payment
        total_interest += b.monthly_interest_payment

        # Weighted average interest computation
        if b.interest_payment_percentage and b.lender_amount:
            weighted_interest_sum += b.interest_payment_percentage * b.lender_amount

        # Breakdown by type
        if b.borrowing_type in by_type:
            by_type[b.borrowing_type]['count'] += 1
            by_type[b.borrowing_type]['amount'] += b.lender_amount

    average_interest_rate = (
        weighted_interest_sum / total_amount if total_amount > 0 else Decimal('0.00')
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return {
        'total_borrowings': total_borrowings,
        'total_amount': total_amount.quantize(Decimal('0.01')),
        'total_monthly_principal': total_principal.quantize(Decimal('0.01')),
        'total_monthly_interest': total_interest.quantize(Decimal('0.01')),
        'average_interest_rate': average_interest_rate,
        'by_type': {
            k: {
                'count': v['count'],
                'amount': v['amount'].quantize(Decimal('0.01')),
                'percentage': (
                    (v['amount'] / total_amount * 100).quantize(Decimal('0.01'))
                    if total_amount > 0 else Decimal('0.00')
                ),
            }
            for k, v in by_type.items()
        },
    }
