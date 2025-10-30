# /root/bond_platform/Backend/apps/utils/swagger_base.py
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.views import APIView



class SwaggerParamAPIView(APIView):
    """Base APIView that safely adds Swagger parameters (for DRF Spectacular)."""
    swagger_parameters = []

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)

        # Only decorate methods that actually exist (e.g., GET, POST)
        if cls.swagger_parameters:
            existing_methods = {m.lower() for m in ['get', 'post', 'put', 'patch', 'delete'] if hasattr(cls, m)}
            for method in existing_methods:
                method_view = getattr(cls, method, None)
                if method_view:
                    decorated = extend_schema(parameters=cls.swagger_parameters)(method_view)
                    setattr(cls, method, decorated)
        return view
