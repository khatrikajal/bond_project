from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from apps.bond_estimate.models.borrowing_details import BorrowingType, RepaymentTerms


# ---------------------------------------------------------------
# Monthly Interest Calculation
# ---------------------------------------------------------------
def calculate_monthly_interest(principal: Decimal, annual_rate: Decimal) -> Decimal:
    """
    Calculate the monthly interest payment from principal and annual rate.
    """
    try:
        if not principal or not annual_rate:
            return Decimal('0.00')

        monthly_interest = (
            Decimal(principal) * Decimal(annual_rate) / Decimal('100')
        ) / Decimal('12')

        return monthly_interest.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    except (InvalidOperation, ZeroDivisionError):
        return Decimal('0.00')


# ---------------------------------------------------------------
# EMI Calculation
# ---------------------------------------------------------------
def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
    """
    Calculate EMI using the standard loan formula.
    """
    try:
        principal = Decimal(principal)
        annual_rate = Decimal(annual_rate)
        tenure_months = int(tenure_months)

        if principal <= 0 or tenure_months <= 0:
            return Decimal('0.00')

        monthly_rate = annual_rate / Decimal('1200')

        if monthly_rate == 0:
            emi = principal / tenure_months
        else:
            factor = (1 + monthly_rate) ** tenure_months
            emi = (principal * monthly_rate * factor) / (factor - 1)

        return emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    except (InvalidOperation, ZeroDivisionError, ValueError):
        return Decimal('0.00')


# ---------------------------------------------------------------
# Validation for Borrowing Data
# ---------------------------------------------------------------
def validate_borrowing_data(data: dict):
    """
    Validate the borrowing payload.
    """
    errors = []

    required_fields = ['company_id', 'lender_name', 'lender_amount', 'borrowing_type', 'repayment_terms']

    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            errors.append(f"{field} is required.")

    # Validate amount
    try:
        lender_amount = Decimal(str(data.get('lender_amount', '0')))
        if lender_amount <= 0:
            errors.append("Lender amount must be greater than 0.")
    except InvalidOperation:
        errors.append("Invalid lender_amount format.")

    # Validate optional numeric fields
    num_fields = ['monthly_principal_payment', 'monthly_interest_payment', 'interest_payment_percentage']

    for key in num_fields:
        if key in data and data[key] not in [None, ""]:
            try:
                val = Decimal(str(data[key]))
                if val < 0:
                    errors.append(f"{key} cannot be negative.")
                if key == 'interest_payment_percentage' and val > 100:
                    errors.append("Interest percentage cannot exceed 100.")
            except InvalidOperation:
                errors.append(f"Invalid numeric value for {key}.")

    # Validate borrowing_type
    if data.get('borrowing_type') not in [c[0] for c in BorrowingType.choices]:
        errors.append(
            f"Invalid borrowing_type. Valid: {', '.join([c[0] for c in BorrowingType.choices])}"
        )

    # Validate repayment_terms
    if data.get('repayment_terms') not in [c[0] for c in RepaymentTerms.choices]:
        errors.append(
            f"Invalid repayment_terms. Valid: {', '.join([c[0] for c in RepaymentTerms.choices])}"
        )

    return (len(errors) == 0, errors)


# ---------------------------------------------------------------
# Borrowing Summary Calculation
# ---------------------------------------------------------------
def calculate_borrowing_summary(borrowings):
    """
    Calculate aggregated borrowing summary.
    """
    total_borrowings = len(borrowings)
    total_amount = Decimal('0.00')
    total_principal = Decimal('0.00')
    total_interest = Decimal('0.00')
    weighted_interest_sum = Decimal('0.00')

    by_type = {
        choice[0]: {'count': 0, 'amount': Decimal('0.00')}
        for choice in BorrowingType.choices
    }

    for b in borrowings:
        total_amount += b.lender_amount
        total_principal += b.monthly_principal_payment
        total_interest += b.monthly_interest_payment

        if b.interest_payment_percentage and b.lender_amount:
            weighted_interest_sum += b.interest_payment_percentage * b.lender_amount

        # Type breakdown
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
                )
            }
            for k, v in by_type.items()
        }
    }
