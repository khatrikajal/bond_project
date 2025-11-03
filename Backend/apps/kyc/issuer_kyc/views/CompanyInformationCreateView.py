from rest_framework.views import APIView
from ..serializers.CompanyInfoSerializer import CompanyInfoSerializer
from rest_framework.response import Response
from rest_framework import status

class CompanyInformationCreateView(APIView):

    def post(self,request):
        serializer = CompanyInfoSerializer(data=request.data,CONTEXT={'request': request})

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

