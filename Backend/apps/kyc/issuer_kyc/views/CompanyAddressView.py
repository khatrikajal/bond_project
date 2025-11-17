
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework import status,serializers
# from django.utils import timezone
# from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
# from apps.kyc.issuer_kyc.models.CompanyInformationModel import CompanyInformation
# from apps.kyc.issuer_kyc.serializers.CompanyAddressSerializer import CompanyAddressSerializer
# from rest_framework.permissions import IsAuthenticated
# from apps.kyc.issuer_kyc.utils.extract_address import extract_address_from_bill 



# class ComapnyAdressAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     # ✅ GET method
#     def get(self, request, company_id):
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id)
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {"success": False, "error": "Company not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         addresses = CompanyAddress.objects.filter(company=company)

#         if not addresses.exists():
#             return Response(
#                 {"success": False, "message": "No addresses found for this company."},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         both_address = addresses.filter(address_type=2).first()
#         if both_address:
#             data = {
#                 "success": True,
#                 "addresses": {
#                     "registered": {
#                         "address_id": both_address.address_id,
#                         "registered_office": both_address.registered_office_address,
#                         "city": both_address.city,
#                         "state_ut": both_address.state_ut,
#                         "pin_code": both_address.pin_code,
#                         "country": both_address.country,
#                         "contact_email": both_address.company_contact_email,
#                         "contact_phone": both_address.company_contact_phone,
#                     },
#                     "correspondence": {
#                         "address_id": both_address.address_id,
#                         "registered_office": both_address.registered_office_address,
#                         "city": both_address.city,
#                         "state_ut": both_address.state_ut,
#                         "pin_code": both_address.pin_code,
#                         "country": both_address.country,
#                         "contact_email": both_address.company_contact_email,
#                         "contact_phone": both_address.company_contact_phone,
#                     }
#                 }
#             }
#             return Response(data, status=status.HTTP_200_OK)

#         # Otherwise check separate REGISTERED & CORRESPONDENCE
#         registered = addresses.filter(address_type=0).first()
#         correspondence = addresses.filter(address_type=1).first()

#         data = {
#             "success": True,
#             "addresses": {
#                 "registered": None,
#                 "correspondence": None
#             }
#         }

#         if registered:
#             data["addresses"]["registered"] = {
#                 "address_id": registered.address_id,
#                 "registered_office": registered.registered_office_address,
#                 "city": registered.city,
#                 "state_ut": registered.state_ut,
#                 "pin_code": registered.pin_code,
#                 "country": registered.country,
#                 "contact_email": registered.company_contact_email,
#                 "contact_phone": registered.company_contact_phone,
#             }

#         if correspondence:
#             data["addresses"]["correspondence"] = {
#                 "address_id": correspondence.address_id,
#                 "registered_office": correspondence.registered_office_address,
#                 "city": correspondence.city,
#                 "state_ut": correspondence.state_ut,
#                 "pin_code": correspondence.pin_code,
#                 "country": correspondence.country,
#                 "contact_email": correspondence.company_contact_email,
#                 "contact_phone": correspondence.company_contact_phone,
#             }

#         return Response(data, status=status.HTTP_200_OK)


#     def post(self, request, company_id):
#             # --- 1️⃣ Check company existence ---
#             try:
#                 company = CompanyInformation.objects.get(company_id=company_id)
#             except CompanyInformation.DoesNotExist:
#                 return Response(
#                     {"success": False, "error": "Company not found"},
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#             data = request.data.copy()
#             files = request.FILES

#             # Ensure boolean conversion
#             is_same_address = str(data.get("is_same_address", "true")).lower() in ["true", "1", "yes"]

#             created_records = []

#             # --- 2️⃣ Case 1: Same Address (Single Row, Type=2) ---
#             if is_same_address:
#                 address_data = {
#                     "company": company.company_id,
#                     "registered_office_address": data.get("registered_office"),
#                     "city": data.get("city"),
#                     "state_ut": data.get("state_ut"),
#                     "pin_code": data.get("pin_code"),
#                     "country": data.get("country", "India"),
#                     "company_contact_email": data.get("contact_email"),
#                     "company_contact_phone": data.get("contact_phone"),
#                     "address_type": 2,  # ✅ same address
#                 }

#                 if files.get("address_proof_file"):
#                     address_data["address_proof_file"] = files["address_proof_file"]

#                 serializer = CompanyAddressSerializer(data=address_data, context={"request": request})
#                 if serializer.is_valid():
#                     serializer.save(company=company)
#                     created_records.append(serializer.data)
#                 else:
#                     return Response(
#                         {"success": False, "errors": serializer.errors},
#                         status=status.HTTP_400_BAD_REQUEST,
#                     )

#             # --- 3️⃣ Case 2: Different Addresses (Two Rows) ---
#             else:
#                 # Common file handling logic:
#                 address_file = files.get("address_proof_file", None)
#                 corr_file = files.get("correspondence_address_proof_file", None)

#                 # If only one file uploaded → use same file for both
#                 if not corr_file and address_file:
#                     corr_file = address_file

#                 # --- Registered Address ---
#                 reg_data = {
#                     "company": company.company_id,
#                     "registered_office_address": data.get("registered_office"),
#                     "city": data.get("city"),
#                     "state_ut": data.get("state_ut"),
#                     "pin_code": data.get("pin_code"),
#                     "country": data.get("country", "India"),
#                     "company_contact_email": data.get("contact_email"),
#                     "company_contact_phone": data.get("contact_phone"),
#                     "address_type": 0,
#                 }
#                 if address_file:
#                     reg_data["address_proof_file"] = address_file

#                 reg_serializer = CompanyAddressSerializer(data=reg_data, context={"request": request})
#                 if reg_serializer.is_valid():
#                     reg_instance = reg_serializer.save(company=company)
#                     created_records.append(reg_serializer.data)
#                 else:
#                     return Response(
#                         {"success": False, "errors": reg_serializer.errors},
#                         status=status.HTTP_400_BAD_REQUEST,
#                     )

#                 # --- Correspondence Address ---
#                 corr_data = {
#                     "company": company.company_id,
#                     "registered_office_address": data.get("correspondence_address"),
#                     "city": data.get("correspondence_city"),
#                     "state_ut": data.get("correspondence_state_ut"),
#                     "pin_code": data.get("correspondence_pin_code"),
#                     "country": data.get("correspondence_country", "India"),
#                     "company_contact_email": data.get("correspondence_email"),
#                     "company_contact_phone": data.get("correspondence_phone"),
#                     "address_type": 1,
#                 }
#                 if corr_file:
#                     corr_data["address_proof_file"] = corr_file

#                 corr_serializer = CompanyAddressSerializer(data=corr_data, context={"request": request})
#                 if corr_serializer.is_valid():
#                     corr_instance = corr_serializer.save(company=company)
#                     created_records.append(corr_serializer.data)
#                 else:
#                     return Response(
#                         {"success": False, "errors": corr_serializer.errors},
#                         status=status.HTTP_400_BAD_REQUEST,
#                     )

#             # --- 4️⃣ Return Success Response ---
#             return Response(
#                 {
#                     "success": True,
#                     "message": "Company address added successfully",
#                     "created_at": timezone.now(),
#                     "data": created_records,
#                 },
#                 status=status.HTTP_201_CREATED,
#             )

#     def put(self, request, company_id):
#         # --- 1️⃣ Validate company existence ---
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id)
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {"success": False, "error": "Company not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         data = request.data.copy()
#         files = request.FILES
#         # normalize boolean (frontend might send string "true"/"false")
#         is_same_address = str(data.get("is_same_address", "true")).lower() in ["true", "1", "yes"]

#         updated_records = []

#         # --- 2️⃣ Case 1: Same address (type = 2) ---
#         if is_same_address:
#             try:
#                 address_instance = CompanyAddress.objects.get(company=company, address_type=2, del_flag=0)
#             except CompanyAddress.DoesNotExist:
#                 return Response(
#                     {"success": False, "error": "No BOTH address found"},
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#             address_data = {
#                 "registered_office_address": data.get("registered_office"),
#                 "city": data.get("city"),
#                 "state_ut": data.get("state_ut"),
#                 "pin_code": data.get("pin_code"),
#                 "country": data.get("country", "India"),
#                 "company_contact_email": data.get("contact_email"),
#                 "company_contact_phone": data.get("contact_phone"),
#             }

#             # update file if provided
#             address_file = files.get("address_proof_file")
#             if address_file:
#                 address_data["address_proof_file"] = address_file

#             serializer = CompanyAddressSerializer(
#                 address_instance, data=address_data, partial=True, context={"request": request}
#             )
#             if serializer.is_valid():
#                 serializer.save()
#                 updated_records.append(serializer.data)
#             else:
#                 return Response(
#                     {"success": False, "errors": serializer.errors},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # --- 3️⃣ Case 2: Different addresses (type = 0 and type = 1) ---
#         else:
#             # --- Registered Address (type = 0) ---
#             try:
#                 reg_instance = CompanyAddress.objects.get(company=company, address_type=0, del_flag=0)
#             except CompanyAddress.DoesNotExist:
#                 return Response(
#                     {"success": False, "error": "No REGISTERED address found"},
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#             reg_data = {
#                 "registered_office_address": data.get("registered_office"),
#                 "city": data.get("city"),
#                 "state_ut": data.get("state_ut"),
#                 "pin_code": data.get("pin_code"),
#                 "country": data.get("country", "India"),
#                 "company_contact_email": data.get("contact_email"),
#                 "company_contact_phone": data.get("contact_phone"),
#             }

#             reg_file = files.get("address_proof_file")
#             if reg_file:
#                 reg_data["address_proof_file"] = reg_file

#             reg_serializer = CompanyAddressSerializer(
#                 reg_instance, data=reg_data, partial=True, context={"request": request}
#             )
#             if reg_serializer.is_valid():
#                 reg_serializer.save()
#                 updated_records.append(reg_serializer.data)
#             else:
#                 return Response(
#                     {"success": False, "errors": reg_serializer.errors},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # --- Correspondence Address (type = 1) ---
#             try:
#                 corr_instance = CompanyAddress.objects.get(company=company, address_type=1, del_flag=0)
#             except CompanyAddress.DoesNotExist:
#                 return Response(
#                     {"success": False, "error": "No CORRESPONDENCE address found"},
#                     status=status.HTTP_404_NOT_FOUND
#                 )

#             corr_data = {
#                 "registered_office_address": data.get("correspondence_address"),
#                 "city": data.get("correspondence_city"),
#                 "state_ut": data.get("correspondence_state_ut"),
#                 "pin_code": data.get("correspondence_pin_code"),
#                 "country": data.get("correspondence_country", "India"),
#                 "company_contact_email": data.get("correspondence_email"),
#                 "company_contact_phone": data.get("correspondence_phone"),
#             }

#             # use correspondence file if provided, else fallback to common file
#             corr_file = files.get("correspondence_address_proof_file") or files.get("address_proof_file")
#             if corr_file:
#                 corr_data["address_proof_file"] = corr_file

#             corr_serializer = CompanyAddressSerializer(
#                 corr_instance, data=corr_data, partial=True, context={"request": request}
#             )
#             if corr_serializer.is_valid():
#                 corr_serializer.save()
#                 updated_records.append(corr_serializer.data)
#             else:
#                 return Response(
#                     {"success": False, "errors": corr_serializer.errors},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # --- 4️⃣ Success response ---
#         return Response(
#             {
#                 "success": True,
#                 "message": "Company address updated successfully",
#                 "updated_at": timezone.now(),
#                 "data": updated_records,
#             },
#             status=status.HTTP_200_OK,
#         )
    
#     def delete(self, request, company_id):
#         try:
#             company = CompanyInformation.objects.get(company_id=company_id)
#         except CompanyInformation.DoesNotExist:
#             return Response(
#                 {"success": False, "error": "Company not found"},
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         serializer = CompanyAddressSerializer()
        

#         try:
#             deleted_records = serializer.soft_delete_all(company)
#             return Response(
#                 {
#                     "success": True,
#                     "message": "All active company addresses soft-deleted successfully",
#                     "deleted_records": deleted_records,
#                     "deleted_at": timezone.now(),
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except serializers.ValidationError as e:
#             return Response(
#                 {"success": False, "errors": e.detail},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         except Exception as e:
#             return Response(
#                 {"success": False, "error": f"Unexpected error: {str(e)}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
        
    
#     def _create_address(self, request):
#         data = request.data
#         is_same_address = data.get("is_same_address", True)
#         created_records = []

#         # Your existing company/address creation logic
#         # (unchanged from your previous code)
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
from rest_framework import status, serializers
from django.utils import timezone
from apps.kyc.issuer_kyc.models.CompanyAdressModel import CompanyAddress
from apps.kyc.issuer_kyc.serializers.CompanyAddressSerializer import CompanyAddressSerializer
from rest_framework.permissions import IsAuthenticated
from apps.kyc.issuer_kyc.utils.extract_address import extract_address_from_bill
from apps.mixins.CompanyScopedMixin import CompanyScopedMixin
from apps.utils.get_company_from_token import get_company_from_token

class ComapnyAdressAPIView( APIView):
    permission_classes = [IsAuthenticated]

    # ✅ GET method
    def get(self, request):
        company = get_company_from_token(request)   # <-- from mixin

        addresses = CompanyAddress.objects.filter(company=company)

        if not addresses.exists():
            return Response(
                {"success": False, "message": "No addresses found for this company."},
                status=status.HTTP_404_NOT_FOUND
            )

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

    # ✅ POST method
    def post(self, request):
        company = get_company_from_token(request)   # <-- from mixin

        data = request.data.copy()
        files = request.FILES

        is_same_address = str(data.get("is_same_address", "true")).lower() in ["true", "1", "yes"]
        created_records = []

        # --- Same Address Case ---
        if is_same_address:
            address_data = {
                "company": company.company_id,
                "registered_office_address": data.get("registered_office"),
                "city": data.get("city"),
                "state_ut": data.get("state_ut"),
                "pin_code": data.get("pin_code"),
                "country": data.get("country", "India"),
                "company_contact_email": data.get("contact_email"),
                "company_contact_phone": data.get("contact_phone"),
                "address_type": 2,
            }

            if "address_proof_file" in files:
                address_data["address_proof_file"] = files["address_proof_file"]

            serializer = CompanyAddressSerializer(data=address_data, context={"request": request})
            if serializer.is_valid():
                serializer.save(company=company)
                created_records.append(serializer.data)
            else:
                return Response(
                    {"success": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # --- Different Address Case ---
        else:
            address_file = files.get("address_proof_file")
            corr_file = files.get("correspondence_address_proof_file") or address_file

            # Registered
            reg_data = {
                "company": company.company_id,
                "registered_office_address": data.get("registered_office"),
                "city": data.get("city"),
                "state_ut": data.get("state_ut"),
                "pin_code": data.get("pin_code"),
                "country": data.get("country", "India"),
                "company_contact_email": data.get("contact_email"),
                "company_contact_phone": data.get("contact_phone"),
                "address_type": 0,
            }
            if address_file:
                reg_data["address_proof_file"] = address_file

            reg_serializer = CompanyAddressSerializer(data=reg_data, context={"request": request})
            if reg_serializer.is_valid():
                reg_serializer.save(company=company)
                created_records.append(reg_serializer.data)
            else:
                return Response(
                    {"success": False, "errors": reg_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Correspondence
            corr_data = {
                "company": company.company_id,
                "registered_office_address": data.get("correspondence_address"),
                "city": data.get("correspondence_city"),
                "state_ut": data.get("correspondence_state_ut"),
                "pin_code": data.get("correspondence_pin_code"),
                "country": data.get("correspondence_country", "India"),
                "company_contact_email": data.get("correspondence_email"),
                "company_contact_phone": data.get("correspondence_phone"),
                "address_type": 1,
            }
            if corr_file:
                corr_data["address_proof_file"] = corr_file

            corr_serializer = CompanyAddressSerializer(data=corr_data, context={"request": request})
            if corr_serializer.is_valid():
                corr_serializer.save(company=company)
                created_records.append(corr_serializer.data)
            else:
                return Response(
                    {"success": False, "errors": corr_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                "success": True,
                "message": "Company address added successfully",
                "created_at": timezone.now(),
                "data": created_records,
            },
            status=status.HTTP_201_CREATED,
        )

    # ✅ PUT method
    def put(self, request, company_id=None):
        company = get_company_from_token(request)   # <-- from mixin

        data = request.data.copy()
        files = request.FILES

        is_same_address = str(data.get("is_same_address", "true")).lower() in ["true", "1", "yes"]
        updated_records = []

        # Same Address Case
        if is_same_address:
            try:
                address_instance = CompanyAddress.objects.get(company=company, address_type=2, del_flag=0)
            except CompanyAddress.DoesNotExist:
                return Response(
                    {"success": False, "error": "No BOTH address found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            address_data = {
                "registered_office_address": data.get("registered_office"),
                "city": data.get("city"),
                "state_ut": data.get("state_ut"),
                "pin_code": data.get("pin_code"),
                "country": data.get("country", "India"),
                "company_contact_email": data.get("contact_email"),
                "company_contact_phone": data.get("contact_phone"),
            }

            if "address_proof_file" in files:
                address_data["address_proof_file"] = files["address_proof_file"]

            serializer = CompanyAddressSerializer(address_instance, data=address_data, partial=True,
                                                  context={"request": request})
            if serializer.is_valid():
                serializer.save()
                updated_records.append(serializer.data)
            else:
                return Response(
                    {"success": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Different Address Case
        else:
            try:
                reg_instance = CompanyAddress.objects.get(company=company, address_type=0, del_flag=0)
                corr_instance = CompanyAddress.objects.get(company=company, address_type=1, del_flag=0)
            except CompanyAddress.DoesNotExist:
                return Response(
                    {"success": False, "error": "Address records not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Registered update
            reg_data = {
                "registered_office_address": data.get("registered_office"),
                "city": data.get("city"),
                "state_ut": data.get("state_ut"),
                "pin_code": data.get("pin_code"),
                "country": data.get("country", "India"),
                "company_contact_email": data.get("contact_email"),
                "company_contact_phone": data.get("contact_phone"),
            }

            if "address_proof_file" in files:
                reg_data["address_proof_file"] = files["address_proof_file"]

            reg_serializer = CompanyAddressSerializer(reg_instance, data=reg_data, partial=True,
                                                      context={"request": request})
            if reg_serializer.is_valid():
                reg_serializer.save()
                updated_records.append(reg_serializer.data)
            else:
                return Response(
                    {"success": False, "errors": reg_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Correspondence update
            corr_data = {
                "registered_office_address": data.get("correspondence_address"),
                "city": data.get("correspondence_city"),
                "state_ut": data.get("correspondence_state_ut"),
                "pin_code": data.get("correspondence_pin_code"),
                "country": data.get("correspondence_country", "India"),
                "company_contact_email": data.get("correspondence_email"),
                "company_contact_phone": data.get("correspondence_phone"),
            }

            corr_file = files.get("correspondence_address_proof_file") or files.get("address_proof_file")
            if corr_file:
                corr_data["address_proof_file"] = corr_file

            corr_serializer = CompanyAddressSerializer(corr_instance, data=corr_data, partial=True,
                                                       context={"request": request})
            if corr_serializer.is_valid():
                corr_serializer.save()
                updated_records.append(corr_serializer.data)
            else:
                return Response(
                    {"success": False, "errors": corr_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {
                "success": True,
                "message": "Company address updated successfully",
                "updated_at": timezone.now(),
                "data": updated_records,
            },
            status=status.HTTP_200_OK,
        )

    # DELETE
    def delete(self, request, company_id=None):
        company = get_company_from_token(request)   # <-- from mixin

        serializer = CompanyAddressSerializer()

        try:
            deleted_records = serializer.soft_delete_all(company)
            return Response(
                {
                    "success": True,
                    "message": "All active company addresses soft-deleted successfully",
                    "deleted_records": deleted_records,
                    "deleted_at": timezone.now(),
                },
                status=status.HTTP_200_OK,
            )
        except serializers.ValidationError as e:
            return Response(
                {"success": False, "errors": e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"success": False, "error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

