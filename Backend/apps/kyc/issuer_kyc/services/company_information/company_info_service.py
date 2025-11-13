import logging
import requests
from django.conf import settings
from apps.kyc.issuer_kyc.models import CompanyInformation

logger = logging.getLogger(__name__)

class CompanyInfoService:
    """
    Handles fetching company data from a third-party API or fallback dummy data.
    """

    THIRD_PARTY_API_URL = getattr(settings, "THIRD_PARTY_CIN_API_URL", None)
    THIRD_PARTY_API_KEY = getattr(settings, "THIRD_PARTY_CIN_API_KEY", None)

    @classmethod
    def get_company_data_by_cin(cls, cin: str):
        """
        Returns company data by CIN.
        - First tries to fetch from third-party API (if configured)
        - Falls back to local DB or dummy data if API fails
        """

        # If third-party API details are available
        if cls.THIRD_PARTY_API_URL:
            try:
                headers = {"Authorization": f"Bearer {cls.THIRD_PARTY_API_KEY}"} if cls.THIRD_PARTY_API_KEY else {}
                response = requests.get(f"{cls.THIRD_PARTY_API_URL}?cin={cin}", headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Fetched company data from API for CIN: {cin}")
                    return {"source": "external_api", "data": data}

                logger.warning(f"Third-party API returned {response.status_code} for CIN: {cin}")

            except Exception as e:
                logger.exception(f"Error fetching company data from API for CIN: {cin}: {e}")

        # --- Fallback: local DB ---
        company = CompanyInformation.active.filter(corporate_identification_number=cin).first()
        if company:
            logger.info(f"Fetched company data from local DB for CIN: {cin}")
            return {
                "source": "local_db",
                "data": {
                    "company_name": company.company_name,
                    "date_of_incorporation": company.date_of_incorporation,
                    "place_of_incorporation": company.place_of_incorporation,
                    "state_of_incorporation": company.state_of_incorporation,
                    "entity_type": company.entity_type,
                    "company_pan_number": company.company_pan_number,
                    "gstin": company.gstin,
                },
            }

        # --- Fallback: Dummy data ---
        logger.info(f"No data found for CIN: {cin}. Returning dummy data.")
        dummy_data = {
            "company_name": "ABC Pvt Ltd",
            "date_of_incorporation": "2010-01-15",
            "place_of_incorporation": "Mumbai",
            "state_of_incorporation": "Maharashtra",
            "entity_type": "Private Limited",
            "company_pan_number": "ABCDE1234F",
            "gstin": "27ABCDE1234F1Z5",
        }
        return {"source": "dummy_data", "data": dummy_data}
