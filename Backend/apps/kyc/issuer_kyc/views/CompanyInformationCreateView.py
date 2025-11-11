from rest_framework.views import APIView
from ..serializers.CompanyInfoSerializer import CompanyInfoSerializer,PanExtractionSerializer,CompanyInfoGetSerializer,CompanyInfoUpdateSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from ..models import CompanyInformation,CompanyOnboardingApplication

class CompanyInformationCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        serializer = CompanyInfoSerializer(data=request.data, context={'request': request})


        if serializer.is_valid():
            data = serializer.save()
            return Response( { 
                "status": "success", 
                "message": data["message"], 
                "data": { 
                    "company_id": data["company_id"], 
                    "company_name": data["company_name"], 
                    "company_pan_number": data["company_pan_number"],
                     
                      "pan_holder_name": data["pan_holder_name"], 
                      "date_of_birth": data["date_of_birth"],
                        },
                          }, 
                      status=status.HTTP_201_CREATED, )
        return Response( {"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST, )
    


class PanExtractionView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = PanExtractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_200_OK)
    

class CompanyInfoGetView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request,company_id):
        try:
            company = CompanyInformation.objects.get(company_id=company_id,user=request.user)
        except CompanyInformation.DoesNotExist:
            return Response({
                "status":"error","message":"Company information not found."
            },status=status.HTTP_404_NOT_FOUND)
        serializer = CompanyInfoGetSerializer(company)
        return Response({
            "status":"success",
            "data":serializer.data,
        },status=status.HTTP_200_OK)
    
class CompanyInformationUpdateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, company_id):
        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
        except CompanyInformation.DoesNotExist:
            return Response(
                {"status": "error", "message": "Company information not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CompanyInfoUpdateSerializer(instance=company, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            data = serializer.save()
            return Response(
                {
                    "status": "success",
                    "message": data["message"],
                    "data": {
                        "company_id": data["company_id"],
                        "company_name": data["company_name"],
                        "company_pan_number": data["company_pan_number"],
                        "pan_holder_name": data["pan_holder_name"],
                        "date_of_birth": data["date_of_birth"],
                    },
                },
                status=status.HTTP_200_OK,
            )

        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class CompanyInfoDeleteView(APIView):
    authentication_classes =[JWTAuthentication]
    permission_classes =[IsAuthenticated]

    def delete(self,request,company_id):
        try:
            company = CompanyInformation.objects.get(company_id=company_id, user=request.user)
        except CompanyInformation.DoesNotExist:
            return Response({
                "status": "error", "message": "Company information not found."
            },status=status.HTTP_404_NOT_FOUND)
        
        
        # CompanyOnboardingApplication.objects.filter(company_information=company,user=request.user).delete()

        company.delete()

        return Response({
            "status": "success",
                "message": "Company information deleted successfully."
        },status=status.HTTP_200_OK)



