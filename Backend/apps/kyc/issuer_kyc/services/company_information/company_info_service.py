import logging
import requests
from django.conf import settings
from apps.kyc.issuer_kyc.models import CompanyInformation

logger = logging.getLogger(__name__)


class CompanyInfoService:
    """
    Handles fetching company data from a third-party CIN API,
    falling back to local DB, and finally dummy sample data.
    """

    THIRD_PARTY_API_URL = getattr(settings, "THIRD_PARTY_CIN_API_URL", None)
    THIRD_PARTY_API_KEY = getattr(settings, "THIRD_PARTY_CIN_API_KEY", None)

    @classmethod
    def get_company_data_by_cin(cls, cin: str):
        """
        Return company details using CIN.
        Priority:
            1. Third-party API
            2. Local DB (company_kyc)
            3. Dummy data fallback
        """

        # ----------------------------------------------------
        # 1️⃣ EXTERNAL CIN API Lookup
        # ----------------------------------------------------
        if cls.THIRD_PARTY_API_URL:
            try:
                headers = {
                    "Authorization": f"Bearer {cls.THIRD_PARTY_API_KEY}"
                } if cls.THIRD_PARTY_API_KEY else {}

                response = requests.get(
                    f"{cls.THIRD_PARTY_API_URL}?cin={cin}",
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    logger.info(f"[CIN API] Success for CIN={cin}")
                    return {
                        "source": "external_api",
                        "data": response.json()
                    }

                logger.warning(
                    f"[CIN API] Non-200 response ({response.status_code}) for CIN={cin}"
                )

            except Exception as e:
                logger.exception(f"[CIN API] CIN={cin} → Error: {e}")

        # ----------------------------------------------------
        # 2️⃣ LOCAL DATABASE LOOKUP
        # ----------------------------------------------------
        company = CompanyInformation.active.filter(
            corporate_identification_number=cin
        ).first()

        if company:
            logger.info(f"[Local DB] CIN found locally → CIN={cin}")
            return {
                "source": "local_db",
                "data": {
                    "company_name": company.company_name,
                    "date_of_incorporation": company.date_of_incorporation,
                    "city_of_incorporation": company.city_of_incorporation,
                    "state_of_incorporation": company.state_of_incorporation,
                    "country_of_incorporation": company.country_of_incorporation,
                    "sector": company.sector,
                    "entity_type": company.entity_type,
                    "company_pan_number": company.company_pan_number,
                    "gstin": company.gstin,
                },
            }

        # ----------------------------------------------------
        # 3️⃣ DUMMY FALLBACK (last fallback)
        # ----------------------------------------------------
        logger.info(f"[Fallback] CIN={cin} not found → Returning dummy data")

        dummy_data = {
            "company_name": "ABC Pvt Ltd",
            "date_of_incorporation": "2010-01-15",
            "city_of_incorporation": "Mumbai",
            "state_of_incorporation": "Maharashtra",
            "country_of_incorporation": "India",
            "sector": "IT_SOFTWARE",
            "entity_type": "PRIVATE_LTD",
            "company_pan_number": "ABCDE1234F",
            "gstin": "27ABCDE1234F1Z5",
        }

        return {"source": "dummy_data", "data": dummy_data}
