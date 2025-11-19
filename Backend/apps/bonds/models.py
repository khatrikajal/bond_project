from django.db import models
from datetime import date

class RatingAgency(models.TextChoices):
    CRISIL = "CRISIL", "CRISIL"
    ICRA = "ICRA", "ICRA"
    CARE = "CARE", "CARE Ratings"
    IND_RA = "IND-RA", "India Ratings & Research"
    BWR = "BWR", "Brickwork Ratings"
    ACUITE = "ACUITE", "Acuité Ratings"
    INFOMERICS = "INFOMERICS","Infomerics"

    

class CreditRating(models.TextChoices):
    AAA = "AAA", "AAA"
    AA_PLUS = "AA+", "AA+"
    AA = "AA", "AA"
    AA_MINUS = "AA-", "AA-"
    A_PLUS = "A+", "A+"
    A = "A", "A"
    A_MINUS = "A-", "A-"
    BBB_PLUS = "BBB+", "BBB+"
    BBB = "BBB", "BBB"
    BBB_MINUS = "BBB-", "BBB-"
    BB_PLUS = "BB+", "BB+"
    BB = "BB", "BB"
    BB_MINUS = "BB-", "BB-"
    B_PLUS = "B+", "B+"
    B = "B", "B"
    B_MINUS = "B-", "B-"
    C = "C", "C"
    D = "D", "Default / D"
    UNRATED = "UNRATED", "Unrated / No Rating"

class IssuerType(models.TextChoices):
    CENTRAL_GOVERNMENT = "CENTRAL_GOV", "Central Government"
    STATE_GOVERNMENT = "STATE_GOV", "State Government"
    PSU = "PSU", "Public Sector Undertaking"
    SLU = "SLU", "State Level Undertaking"
    CORPORATE = "CORPORATE", "Corporate / Non-PSU"
    BANK = "BANK", "Bank / NBFC"
    MUNICIPAL = "MUNICIPAL", "Municipal Bonds"

class OptionType(models.TextChoices):
    CALL = "CALL", "Callable"
    PUT = "PUT", "Puttable"
    NONE = "NONE", "None"

class TaxCategory(models.TextChoices):
    TAX_FREE = "TAX_FREE", "Tax Free"
    TAXABLE = "TAXABLE", "Taxable"
    PARTIALLY_TAX_FREE = "PARTIALLY_TAX_FREE", "Partially Tax Free"

class TradingStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    DELISTED = "DELISTED", "Delisted"
    MATURED = "MATURED", "Matured"

class CouponType(models.TextChoices):
    FIXED = "FIXED", "Fixed Rate"
    FLOATING = "FLOATING", "Floating Rate"
    ZERO_COUPON = "ZERO_COUPON", "Zero Coupon"
    STEP_UP = "STEP_UP", "Step Up"
    STEP_DOWN = "STEP_DOWN", "Step Down"

class ISINBasicInfo(models.Model):
    """Basic information for ISIN bonds - frequently accessed fields"""

    # CORE IDENTIFICATION (Must stay)
    isin_code = models.CharField(max_length=12, primary_key=True)
    security_type = models.CharField(max_length=100, null=True, blank=True)
    isin_description = models.TextField(null=True, blank=True)
    issue_description = models.TextField(null=True, blank=True)
    
    # CORE FINANCIALS (Must stay)
    coupon_rate_percent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    ytm_percent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    face_value_rs = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    
    # CORE ISSUER INFO (Must stay)
    issuer_name = models.CharField(max_length=255, null=True, blank=True)
    issuer_type = models.CharField(max_length=20, choices=IssuerType.choices, null=True, blank=True)
    
    # CORE ISSUANCE INFO (Must stay)
    issue_size_lakhs = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    
    # STATUS (Must stay)
    isin_active = models.BooleanField(
        default=True,
        verbose_name="ISIN Active?",
        help_text="Check if the ISIN is active"
    )
    
    # FIELDS MOVED FROM DETAILED TO BASIC (high-frequency access)
    listed_unlisted = models.CharField(max_length=50, null=True, blank=True, help_text="Listed or Unlisted status")
    trading_status = models.CharField(max_length=100, choices=TradingStatus.choices, null=True, blank=True, help_text="Active/Suspended/Delisted status")
    tax_category = models.CharField(max_length=50, choices=TaxCategory.choices, null=True, blank=True, help_text="Tax treatment category")
    secured = models.BooleanField(default=False, help_text="Whether the bond is secured or unsecured")
    transferable = models.BooleanField(default=True, help_text="Whether the bond is transferable")
    primary_exchange = models.CharField(max_length=50, null=True, blank=True, help_text="Primary exchange for trading")
    
    # CANDIDATES FOR MOVING TO DETAILED (but keeping here for compatibility)
    former_name = models.CharField(max_length=255, null=True, blank=True)  
    minimum_investment_rs = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)  
    interest_payment_frequency_raw = models.TextField(null=True, blank=True)  
    interest_payment_frequency = models.CharField(max_length=20, null=True, blank=True)  
    percentage_sold = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)  
    mode_of_issuance = models.CharField(max_length=100, null=True, blank=True)  
    series = models.CharField(max_length=100, null=True, blank=True, help_text="Bond series identifier - stays in basic for identification")
    tax_free = models.BooleanField(default=False, help_text="True if bond is tax-free, False if taxable")  # -> Keep for backward compatibility, use tax_category instead
    option_type = models.CharField(max_length=20, choices=OptionType.choices, null=True, blank=True)  
    
    seniority = models.CharField(max_length=255, null=True, blank=True)
    prepetual = models.BooleanField(default=False, null=True) 
    
    # METADATA (Must stay)
    data_hash = models.CharField(max_length=64, null=True, blank=True)
    record_created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.isin_code} - {self.isin_description}"
    
    class Meta:
        db_table = 'isin_basic_info'
        indexes = [
            models.Index(fields=["ytm_percent"]),
            models.Index(fields=["coupon_rate_percent"]),
            models.Index(fields=["face_value_rs"]),
            models.Index(fields=["interest_payment_frequency"]),
            models.Index(fields=["issuer_type"]),
            models.Index(fields=["listed_unlisted"]),
            models.Index(fields=["trading_status"]),
            models.Index(fields=["tax_category"]),
            models.Index(fields=["secured"]),
            models.Index(fields=["primary_exchange"]),
            models.Index(fields=["series"]),  
            models.Index(fields=["maturity_date"]),  
        ]


class ISINRating(models.Model):
    isin = models.ForeignKey("ISINBasicInfo", on_delete=models.CASCADE, related_name="ratings")
    rating_agency = models.CharField(max_length=100, choices=RatingAgency.choices)
    credit_rating = models.CharField(max_length=10, choices=CreditRating.choices)
    rating_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.isin.isin_code} - {self.rating_agency}: {self.credit_rating}"
    
    class Meta:
        db_table = 'isin_rating'
        unique_together = ("isin", "rating_agency", "rating_date")
        indexes = [
            models.Index(fields=["credit_rating"]),
            models.Index(fields=["credit_rating", "rating_agency"]),
        ]




class ISINDetailedInfo(models.Model):
    """Detailed information for ISIN bonds - normalized from basic info"""
    
    isin = models.OneToOneField(
        ISINBasicInfo, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name="detailed_info"
    )
    
    # Issuance & listing details (MOVED FROM BASIC INFO)
    allotment_date = models.DateField(null=True, blank=True)
    opening_date = models.DateField(null=True, blank=True)
    listing_date = models.DateField(null=True, blank=True)
    bse_date_of_listing = models.DateField(null=True, blank=True)
    nse_date_of_listing = models.DateField(null=True, blank=True, help_text="NSE listing date - moved from basic")
    bse_scrip_code = models.CharField(max_length=50, null=True, blank=True)
    nse_symbol = models.CharField(max_length=50, null=True, blank=True)
    first_interest_payment_date = models.DateField(null=True, blank=True)
    
    # MOVED FROM BASIC INFO - Less frequently accessed fields
    closing_date = models.DateField(null=True, blank=True, help_text="Issue closing date - when subscription closed")
    paid_up_value_rs = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True, help_text="Actual amount paid up per bond")
    
    # Exchange details (removed from basic as primary_exchange moved there)
    listing_exchanges = models.CharField(max_length=255, null=True, blank=True)
    secondary_exchange = models.CharField(max_length=50, null=True, blank=True)
    
    # Bond structure (keep in detailed - complex information)
    coupon_type = models.CharField(max_length=100, choices=CouponType.choices, null=True, blank=True)
    day_count_convention = models.CharField(max_length=100, null=True, blank=True)
    compounding_frequency = models.CharField(max_length=100, null=True, blank=True)
    interest_payment_dates = models.TextField(null=True, blank=True)
    interest_payment_day_convention = models.CharField(max_length=100, null=True, blank=True)
    payment_schedule = models.TextField(null=True, blank=True)
    redemption = models.TextField(null=True, blank=True)
    redemption_premium = models.CharField(max_length=255, null=True, blank=True)
    redemption_payment_day_convention = models.CharField(max_length=255, null=True, blank=True)
    
    # Options (keep in detailed - complex features)
    call_option = models.BooleanField(default=False)
    call_option_date = models.DateField(null=True, blank=True)
    call_notification_period = models.CharField(max_length=255, null=True, blank=True)
    put_option = models.BooleanField(default=False)
    put_option_date = models.DateField(null=True, blank=True)
    put_notification_period = models.CharField(max_length=255, null=True, blank=True)
    buyback_option = models.CharField(max_length=100, null=True, blank=True)
    call_notification = models.BooleanField(default=False)
    
    # Security details - 
    security_collateral = models.TextField(null=True, blank=True)  # Keep detailed
    lock_in_period = models.CharField(max_length=100, null=True, blank=True)  # Keep detailed
    
    # Regulatory/structural - 
    benefit_under_section = models.CharField(max_length=255, null=True, blank=True)  # Keep detailed
    basel_compliant = models.BooleanField(default=False)  # Keep detailed
    use_of_proceeds = models.TextField(null=True, blank=True)  # Keep detailed
    pricing_method = models.TextField(null=True, blank=True)  # Keep detailed
    
    # Market data - 
    market_lot = models.BigIntegerField(null=True, blank=True)  # Keep detailed
    settlement_cycle = models.CharField(max_length=100, null=True, blank=True)  # Keep detailed
    last_traded_price_rs = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    last_traded_date = models.DateField(null=True, blank=True)
    volume_traded = models.BigIntegerField(null=True, blank=True)
    value_traded_lakhs = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    number_of_trades = models.BigIntegerField(null=True, blank=True)
    weighted_avg_price_rs = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    weighted_avg_yield_percent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    current_yield_percent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    
    # Risk/yield measures
    duration_years = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    convexity = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Operational
    demat_requests_pending = models.BigIntegerField(null=True, blank=True)
    services_stopped = models.BooleanField(default=False)
    no_of_bonds_ncd = models.BigIntegerField(null=True, blank=True)
    greenshoe_option = models.BooleanField(default=False)
    oversubscription_multiple = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    percentage_sold_cumulative = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    record_date_day_convention = models.CharField(max_length=255, null=True, blank=True)
    reset_details = models.TextField(null=True, blank=True)
    liquidation_status = models.CharField(max_length=255, null=True, blank=True)
    
    # Derived fields
    due_for_maturity = models.IntegerField(null=True, blank=True, help_text="Days until maturity")
    tenure_years = models.IntegerField(null=True, blank=True)
    tenure_months = models.IntegerField(null=True, blank=True)
    tenure_days = models.IntegerField(null=True, blank=True)
    
    # Metadata
    data_hash = models.CharField(max_length=64, null=True, blank=True)
    record_created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Details for {self.isin.isin_code}"
    
    class Meta:
        db_table = 'isin_detailed_info'
        indexes = [
            models.Index(fields=["coupon_type"]),
            models.Index(fields=["last_traded_date"]),
            models.Index(fields=["basel_compliant"]),
        ]


class CompanyInfo(models.Model):
    """Company/Issuer information - normalized entity"""
    
    company_id = models.AutoField(primary_key=True)
    issuer_name = models.CharField(max_length=255, unique=True)
    issuer_logo = models.URLField(max_length=500, null=True, blank=True)
    issuer_address = models.TextField(null=True, blank=True)
    issuer_type = models.CharField(max_length=50, choices=IssuerType.choices, null=True, blank=True)
    issuer_state = models.CharField(max_length=100, null=True, blank=True)
    issuer_website = models.URLField(max_length=255, null=True, blank=True)
    issuer_logo_url = models.URLField(max_length=500, null=True, blank=True)
    issuer_description = models.TextField(null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    fax_number = models.CharField(max_length=50, null=True, blank=True)
    email_id = models.TextField(null=True, blank=True)
    guaranteed_by = models.TextField(null=True, blank=True)
    registrar = models.CharField(max_length=255, null=True, blank=True)
    
    # Industry classification
    industry_group = models.CharField(max_length=100, null=True, blank=True)
    macro_sector = models.CharField(max_length=100, null=True, blank=True)
    micro_industry = models.CharField(max_length=100, null=True, blank=True)
    product_service_activity = models.TextField(null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    security_code = models.CharField(max_length=50, null=True, blank=True)
    financial_last_updated_at = models.DateField(null=True, blank=True)
    
    # Metadata
    data_hash = models.CharField(max_length=64, null=True, blank=True)
    record_created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.issuer_name
    
    class Meta:
        db_table = 'company_info'
        indexes = [
            models.Index(fields=["issuer_type"]),
            models.Index(fields=["sector"]),
            models.Index(fields=["issuer_state"]),
        ]


class ISINCompanyMap(models.Model):
    """Many-to-many relationship between ISIN and Company with additional metadata"""
    
    isin = models.ForeignKey(ISINBasicInfo, on_delete=models.CASCADE, related_name="company_mappings")
    company = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, related_name="isin_mappings")
    primary_company = models.BooleanField(default=True, help_text="Is this the primary issuer for this ISIN")
    mapped_on = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.isin.isin_code} -> {self.company.issuer_name}"
    
    class Meta:
        db_table = 'isin_company_map'
        unique_together = ("isin", "company")
        indexes = [
            models.Index(fields=["primary_company"]),
        ]


class RTAInfo(models.Model):
    """Registrar and Transfer Agent information"""
    
    rta_id = models.AutoField(primary_key=True)
    rta_name = models.CharField(max_length=255, unique=True)
    rta_bp_id = models.CharField(max_length=50, null=True, blank=True)
    rta_address = models.TextField(null=True, blank=True)
    rta_contact_person = models.CharField(max_length=100, null=True, blank=True)
    rta_phone = models.CharField(max_length=255, null=True, blank=True)
    rta_fax = models.CharField(max_length=50, null=True, blank=True)
    rta_email = models.TextField(null=True, blank=True)
    trustee = models.CharField(max_length=255, null=True, blank=True)
    arrangers = models.TextField(null=True, blank=True)
    im_term_sheet = models.CharField(max_length=500, null=True, blank=True)
    
    # Metadata
    data_hash = models.CharField(max_length=64, null=True, blank=True)
    record_created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.rta_name
    
    class Meta:
        db_table = 'rta_info'


class ISINRTAMap(models.Model):
    """Time-based relationship between ISIN and RTA"""
    
    isin = models.ForeignKey(ISINBasicInfo, on_delete=models.CASCADE, related_name="rta_mappings")
    rta = models.ForeignKey(RTAInfo, on_delete=models.CASCADE, related_name="isin_mappings")
    effective_from = models.DateField(default=date.today)
    effective_to = models.DateField(null=True, blank=True)
    mapped_on = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.isin.isin_code} -> {self.rta.rta_name} (from {self.effective_from})"
    
    class Meta:
        db_table = 'isin_rta_map'
        unique_together = ("isin", "rta", "effective_from")
        indexes = [
            models.Index(fields=["effective_from", "effective_to"]),
        ]


# Additional utility models for better data management
class DataTransformationLog(models.Model):
    """Track data transformation operations"""
    
    operation_type = models.CharField(max_length=50)  # 'ETL', 'SYNC', 'MIGRATION'
    source_table = models.CharField(max_length=100, null=True, blank=True)
    target_table = models.CharField(max_length=100, null=True, blank=True)
    records_processed = models.IntegerField(default=0)
    records_success = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_details = models.TextField(null=True, blank=True)
    execution_time_seconds = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='RUNNING')  # RUNNING, SUCCESS, FAILED
    
    class Meta:
        db_table = 'data_transformation_log'
        indexes = [
            models.Index(fields=["operation_type", "started_at"]),
            models.Index(fields=["status"]),
        ]





class FinancialMetric(models.Model):
    company = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, related_name="financial_metrics")
    name = models.CharField(max_length=50)  # e.g., "Revenue", "PAT", "Debt", "Net Worth"
    data_hash = models.CharField(max_length=64, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company.issuer_name} - {self.name}"

    class Meta:
        db_table = 'financial_metric'
        indexes = [
            models.Index(fields=["name"]),
        ]

class FinancialMetricValue(models.Model):
    metric = models.ForeignKey(FinancialMetric, on_delete=models.CASCADE, related_name="values")
    year = models.IntegerField()  # e.g., 2023
    value = models.DecimalField(max_digits=18, decimal_places=2, null=True)  # e.g., 918700000

    def __str__(self):
        return f"{self.metric.name} - {self.year}: {self.value}"

    class Meta:
        db_table = 'financial_metric_value'
        indexes = [
            models.Index(fields=["year"]),
        ]

class RatioAnalysis(models.Model):
    company = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, related_name="ratio_analyses")
    title = models.CharField(max_length=100)  # e.g., "Capital Adequacy Ratio"
    benchmark = models.CharField(max_length=100)  # e.g., "Minimum 14%"
    assessment = models.CharField(max_length=50)  # e.g., "Good", "Risky"
    description = models.TextField()
    data_hash = models.CharField(max_length=64, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company.issuer_name} - {self.title}"

    class Meta:
        db_table = 'ratio_analysis'
        indexes = [
            models.Index(fields=["title"]),
        ]

class RatioValue(models.Model):
    ratio = models.ForeignKey(RatioAnalysis, on_delete=models.CASCADE, related_name="values")
    year = models.IntegerField()  # e.g., 2023
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # e.g., 25.98

    def __str__(self):
        return f"{self.ratio.title} - {self.year}: {self.value}"

    class Meta:
        db_table = 'ratio_value'
        indexes = [
            models.Index(fields=["year"]),
        ]

class KeyFactor(models.Model):
    company = models.OneToOneField(CompanyInfo, on_delete=models.CASCADE, related_name="key_factors")
    key_factors = models.JSONField(default=list)  # e.g., ["Rapid AUM Growth..."]
    strengths = models.JSONField(default=list)  # e.g., ["Healthy Capitalization"]
    weaknesses = models.JSONField(default=list)  # e.g., ["Rising Delinquencies"]
    data_hash = models.CharField(max_length=64, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Key Factors for {self.company.issuer_name}"

    class Meta:
        db_table = 'key_factor'



# class frontend_contactmessage(models.Model):
#     name = models.CharField(max_length=100)
#     email = models.EmailField()
#     phone_number = models.CharField(max_length=20, blank=True, null=True)
#     message = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.name} - {self.email}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "frontend_contactmessage"



class SnapshotDefinition(models.Model):
    """
    Defines which metrics/ratings/key factors appear in the UI snapshot,
    their display names, order, and type.
    """
    METRIC_TYPE_CHOICES = [
        ('financial', 'Financial Metric'),
        ('rating', 'Credit Rating'),
        ('keyfactor', 'Key Factor / Portfolio Quality'),
    ]

    metric_name = models.CharField(max_length=100, help_text="Internal metric name, e.g., 'AUM', 'PAT'")
    display_name = models.CharField(max_length=200, help_text="UI label for the snapshot")
    order = models.PositiveIntegerField(default=0, help_text="Order in the UI snapshot")
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True, help_text="Optional description for UI display")

    class Meta:
        db_table = 'snapshot_definition'
        ordering = ['order']

    def __str__(self):
        return f"{self.display_name} ({self.metric_name})"