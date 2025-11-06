# from rest_framework import permissions
# from rest_framework.exceptions import PermissionDenied
# from ..models.CompanyInformationModel import CompanyInformation


# class IsAuthenticatedIssuer(permissions.BasePermission):
#     """
#     Custom permission to ensure user is authenticated as an issuer.
#     """
    
#     message = "You must be logged in as an issuer to access this resource."
    
#     def has_permission(self, request, view):
#         """Check if user is authenticated"""
#         if not request.user or not request.user.is_authenticated:
#             return False
        
#         # Add additional role check if you have user roles
#         # if hasattr(request.user, 'role'):
#         #     return request.user.role == 'ISSUER'
        
#         return True


# class IsCompanyOwner(permissions.BasePermission):
#     """
#     Custom permission to ensure user owns the company they're accessing.
#     """
    
#     message = "You do not have permission to access this company's resources."
    
#     def has_permission(self, request, view):
#         """Check basic authentication"""
#         if not request.user or not request.user.is_authenticated:
#             return False
        
#         # Get company_id from URL kwargs
#         company_id = view.kwargs.get('company_id')
        
#         if not company_id:
#             return True  # Let view handle missing company_id
        
#         try:
#             # Check if company exists and user owns it
#             company = CompanyInformation.objects.select_related('user').get(
#                 company_id=company_id,
#                 del_flag=0
#             )
            
#             # Check ownership - compare user IDs
#             if company.user_id != request.user.user_id:
#                 return False
            
#             return True
            
#         except CompanyInformation.DoesNotExist:
#             return False
    
#     def has_object_permission(self, request, view, obj):
#         """Check object-level permission for