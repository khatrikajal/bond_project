import time
import random

class DematService:

    @staticmethod
    def fetch_demat_details_from_pan(pan_number: str) -> dict:
        """
        Fetch demat details using PAN number.
        Currently returns dummy data.
        Future-proof: just replace inside this function with API integration.

        DO NOT CHANGE THE SIGNATURE.
        """

        # ---- FUTURE IMPLEMENTATION TEMPLATE ----
        # response = requests.post(
        #     THIRD_PARTY_URL,
        #     json={"pan": pan_number},
        #     headers={"Authorization": "Bearer token"}
        # )
        # return response.json()

        # ---- DUMMY RESPONSE FOR NOW ----
        return {
            "dp_name": "HDFC Securities Ltd",
            "depository_participant": "NSDL",
            "dp_id": f"DP{random.randint(1000, 9999)}",
            "demat_account_number": f"DEM{random.randint(100000, 999999)}",
            "client_id_bo_id": f"CL{random.randint(10000, 99999)}",
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pan_used": pan_number
        }
