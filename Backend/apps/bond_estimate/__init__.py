"""
Views package for bond_estimate app.
You can organize view classes or functions in separate files.
"""
from django.http import HttpResponse

def index(request):
    return HttpResponse("Bond Estimate App placeholder view ✅")
