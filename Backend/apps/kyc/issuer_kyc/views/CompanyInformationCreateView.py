from rest_framework.views import APIView
from ..serializers.CompanyInfoSerializer import CompanyInfoSerializer,PanExtractionSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

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

