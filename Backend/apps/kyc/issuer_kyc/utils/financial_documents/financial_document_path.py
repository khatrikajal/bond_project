import os
from datetime import datetime


def financial_document_upload_path(instance, filename):
    """
    Generates a future-proof path for storing financial documents.

    Works for:
    - Local MEDIA
    - AWS S3
    - Any object storage backend

    Structure:
    financial_documents/company_<id>/<document_type>/<fy>/<period_code>/<tag>/v<version>_<filename>
    """

    company_id = instance.company.company_id  
    doc_type = instance.document_type
    fy = instance.financial_year

    period_code = instance.period_code or "FULL-YEAR"
    tag = instance.document_tag
    version = instance.version

    sanitized_name = filename.replace(" ", "_")

    return os.path.join(
        "financial_documents",
        f"company_{company_id}",
        doc_type,
        fy,
        period_code,
        tag,
        f"v{version}_{sanitized_name}"
    )
