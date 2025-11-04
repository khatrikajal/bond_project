# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework import status
# from django.utils import timezone
# from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
# from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
# from apps.kyc.issuer_kyc.serializers.CompanyAddressSerializer import CompanyAddressSerializer
# from apps.kyc.issuer_kyc.models.helpers import update_step_state


# class ComapnyAdressAPIView(APIView):
#     """
#     API to add company registered/correspondence address.
#     POST /api/kyc/issuer_kyc/company/<company_id>/address/
#     """

#     def post(self, request, company_id):
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id)
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {"success": False, "error": "Company not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         data = request.data
#         is_same_address = data.get("is_same_address", True)
#         created_records = []

#         if is_same_address:
#             # Same for both REGISTERED + CORRESPONDENCE
#             address_data = {
#                 "company": company.company_id,
#                 "registered_office_address": data.get("registered_office"),
#                 "city": data.get("city"),
#                 "state_ut": data.get("state_ut"),
#                 "pin_code": data.get("pin_code"),
#                 "country": data.get("country", "India"),
#                 "company_contact_email": data.get("contact_email"),
#                 "company_contact_phone": data.get("contact_phone"),
#                 "address_type": 2  # BOTH
#             }

#             serializer = CompanyAddressSerializer(data=address_data)
#             if serializer.is_valid():
#                 serializer.save(company=company)
#                 created_records.append(serializer.data)
#             else:
#                 # Call this before returning
#                 update_step_state(company.company_id, 2)
                
#                 return Response(
#                     {"success": False, "errors": serializer.errors},
#                     status=status.HTTP_400_BAD_REQUEST
#     )

#         else:
#             # Registered Address
#             reg_data = {
#                 "company": company.company_id,
#                 "registered_office_address": data.get("registered_office"),
#                 "city": data.get("city"),
#                 "state_ut": data.get("state_ut"),
#                 "pin_code": data.get("pin_code"),
#                 "country": data.get("country", "India"),
#                 "company_contact_email": data.get("contact_email"),
#                 "company_contact_phone": data.get("contact_phone"),
#                 "address_type": 0  # REGISTERED
#             }

#             reg_serializer = CompanyAddressSerializer(data=reg_data)
#             if reg_serializer.is_valid():
#                 reg_serializer.save(company=company)
#                 created_records.append(reg_serializer.data)
#             else:
#                 return Response(
#                     {"success": False, "errors": reg_serializer.errors},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # Correspondence Address
#             corr_data = {
#                 "company": company.company_id,
#                 "registered_office_address": data.get("correspondence_address"),
#                 "city": data.get("correspondence_city"),
#                 "state_ut": data.get("correspondence_state_ut"),
#                 "pin_code": data.get("correspondence_pin_code"),
#                 "country": data.get("correspondence_country", "India"),
#                 "company_contact_email": data.get("correspondence_email"),
#                 "company_contact_phone": data.get("correspondence_phone"),
#                 "address_type": 1  # CORRESPONDENCE
#             }

#             corr_serializer = CompanyAddressSerializer(data=corr_data)
#             if corr_serializer.is_valid():
#                 corr_serializer.save(company=company)
#                 created_records.append(corr_serializer.data)
#             else:
#                 return Response(
#                     {"success": False, "errors": corr_serializer.errors},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         return Response(
#             {
#                 "success": True,
#                 "message": "Company address added successfully",
#                 "created_at": timezone.now(),
#                 "data": created_records
#             },
#             status=status.HTTP_201_CREATED
#         )


from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
from apps.kyc.issuer_kyc.serializers.CompanyAddressSerializer import CompanyAddressSerializer



class ComapnyAdressAPIView(APIView):
    """
    API to add or fetch company registered/correspondence address.
    POST /api/kyc/issuer_kyc/company/<company_id>/address/
    GET  /api/kyc/issuer_kyc/company/<company_id>/address/
    """

    # ✅ GET method
    def get(self, request, company_id):
        try:
            company = CompanyInformation.objects.get(company_id=company_id)
        except CompanyInformation.DoesNotExist:
            return Response(
                {"success": False, "error": "Company not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        addresses = CompanyAddress.objects.filter(company=company)

        if not addresses.exists():
            return Response(
                {"success": False, "message": "No addresses found for this company."},
                status=status.HTTP_404_NOT_FOUND
            )

        # If company has BOTH (2)
        both_address = addresses.filter(address_type=2).first()
        if both_address:
            data = {
                "success": True,
                "addresses": {
                    "registered": {
                        "address_id": both_address.address_id,
                        "registered_office": both_address.registered_office_address,
                        "city": both_address.city,
                        "state_ut": both_address.state_ut,
                        "pin_code": both_address.pin_code,
                        "country": both_address.country,
                        "contact_email": both_address.company_contact_email,
                        "contact_phone": both_address.company_contact_phone,
                    },
                    "correspondence": {
                        "address_id": both_address.address_id,
                        "registered_office": both_address.registered_office_address,
                        "city": both_address.city,
                        "state_ut": both_address.state_ut,
                        "pin_code": both_address.pin_code,
                        "country": both_address.country,
                        "contact_email": both_address.company_contact_email,
                        "contact_phone": both_address.company_contact_phone,
                    }
                }
            }
            return Response(data, status=status.HTTP_200_OK)

        # Otherwise check separate REGISTERED & CORRESPONDENCE
        registered = addresses.filter(address_type=0).first()
        correspondence = addresses.filter(address_type=1).first()

        data = {
            "success": True,
            "addresses": {
                "registered": None,
                "correspondence": None
            }
        }

        if registered:
            data["addresses"]["registered"] = {
                "address_id": registered.address_id,
                "registered_office": registered.registered_office_address,
                "city": registered.city,
                "state_ut": registered.state_ut,
                "pin_code": registered.pin_code,
                "country": registered.country,
                "contact_email": registered.company_contact_email,
                "contact_phone": registered.company_contact_phone,
            }

        if correspondence:
            data["addresses"]["correspondence"] = {
                "address_id": correspondence.address_id,
                "registered_office": correspondence.registered_office_address,
                "city": correspondence.city,
                "state_ut": correspondence.state_ut,
                "pin_code": correspondence.pin_code,
                "country": correspondence.country,
                "contact_email": correspondence.company_contact_email,
                "contact_phone": correspondence.company_contact_phone,
            }

        return Response(data, status=status.HTTP_200_OK)

    # ✅ POST method (already in your code)
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
        created_records = []

        if is_same_address:
            # Same for both REGISTERED + CORRESPONDENCE
            address_data = {
                "company": company.company_id,
                "registered_office_address": data.get("registered_office"),
                "city": data.get("city"),
                "state_ut": data.get("state_ut"),
                "pin_code": data.get("pin_code"),
                "country": data.get("country", "India"),
                "company_contact_email": data.get("contact_email"),
                "company_contact_phone": data.get("contact_phone"),
                "address_type": 2  # BOTH
            }

            serializer = CompanyAddressSerializer(data=address_data)
            if serializer.is_valid():
                serializer.save(company=company)
                created_records.append(serializer.data)
            else:
                # update_step_state(company.company_id, 2)
                return Response(
                    {"success": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        else:
            # Registered Address
            reg_data = {
                "company": company.company_id,
                "registered_office_address": data.get("registered_office"),
                "city": data.get("city"),
                "state_ut": data.get("state_ut"),
                "pin_code": data.get("pin_code"),
                "country": data.get("country", "India"),
                "company_contact_email": data.get("contact_email"),
                "company_contact_phone": data.get("contact_phone"),
                "address_type": 0
            }

            reg_serializer = CompanyAddressSerializer(data=reg_data)
            if reg_serializer.is_valid():
                reg_serializer.save(company=company)
                created_records.append(reg_serializer.data)
            else:
                return Response(
                    {"success": False, "errors": reg_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Correspondence Address
            corr_data = {
                "company": company.company_id,
                "registered_office_address": data.get("correspondence_address"),
                "city": data.get("correspondence_city"),
                "state_ut": data.get("correspondence_state_ut"),
                "pin_code": data.get("correspondence_pin_code"),
                "country": data.get("correspondence_country", "India"),
                "company_contact_email": data.get("correspondence_email"),
                "company_contact_phone": data.get("correspondence_phone"),
                "address_type": 1
            }

            corr_serializer = CompanyAddressSerializer(data=corr_data)
            if corr_serializer.is_valid():
                corr_serializer.save(company=company)
                created_records.append(corr_serializer.data)
            else:
                return Response(
                    {"success": False, "errors": corr_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {
                "success": True,
                "message": "Company address added successfully",
                "created_at": timezone.now(),
                "data": created_records
            },
            status=status.HTTP_201_CREATED
        )