from rest_framework.response import Response

from rest_framework.views import APIView
    
from rest_framework import status
from django.utils import timezone
from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.serializers import CompanyAddressSerializer

class ComapnyAdressAPIView(APIView):
    """
    POST /api/v1/company/{company_id}/address
    Handles single or double address insertions depending on boolean flag.
    """

    def post(self, request, company_id):
        try:
            company = CompanyInformation.objects.get(company_id=company_id)
        except CompanyInformation.DoesNotExist:
            return Response(
                {"success": False, "error": "Company not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        is_same_address = data.get("is_same_address", True) 

        base_address_data = {
            "company": company.company_id,
            "registered_office_address": data.get("registered_office"),
            "city": data.get("city"),
            "state_ut": data.get("state_ut"),
            "pin_code": data.get("pin_code"),
            "country": data.get("country", "India"),
            "company_contact_email": data.get("contact_email"),
            "company_contact_phone": data.get("contact_phone"),
        }

        created_records = []

        if is_same_address:
            # Create one record (BOTH)
            address = CompanyAddress.objects.create(
                company=company,
                registered_office_address=base_address_data["registered_office_address"],
                city=base_address_data["city"],
                state_ut=base_address_data["state_ut"],
                pin_code=base_address_data["pin_code"],
                country=base_address_data["country"],
                company_contact_email=base_address_data["company_contact_email"],
                company_contact_phone=base_address_data["company_contact_phone"],
                address_type=2,  # BOTH
            )
            created_records.append(address)

        else:
            reg_address = CompanyAddress.objects.create(
                company=company,
                registered_office_address=data.get("registered_office"),
                city=data.get("city"),
                state_ut=data.get("state_ut"),
                pin_code=data.get("pin_code"),
                country=data.get("country", "India"),
                company_contact_email=data.get("contact_email"),
                company_contact_phone=data.get("contact_phone"),
                address_type=0,  # REGISTERED
            )

            corr_address = CompanyAddress.objects.create(
                company=company,
                registered_office_address=data.get("correspondence_address"),
                city=data.get("correspondence_city"),
                state_ut=data.get("correspondence_state_ut"),
                pin_code=data.get("correspondence_pin_code"),
                country=data.get("correspondence_country", "India"),
                company_contact_email=data.get("correspondence_email"),
                company_contact_phone=data.get("correspondence_phone"),
                address_type=1,  # CORRESPONDENCE
            )

            created_records.extend([reg_address, corr_address])

        serializer = CompanyAddressSerializer(created_records, many=True)
        return Response(
            {
                "success": True,
                "message": "Company address added successfully",
                "created_at": timezone.now(),
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )
