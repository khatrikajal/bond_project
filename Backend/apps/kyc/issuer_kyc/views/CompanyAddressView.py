from rest_framework.response import Response

from rest_framework.views import APIView


class ComapnyAdressAPIView(APIView):
    def get(self,*agrs,**kwargs):
        return Response({"status":"sucesss"},200)