"""
Demo view for bond_estimate app.
Displays a simple HTTP response to confirm routing works.
"""
from django.http import HttpResponse

def demo_view(request):
    return HttpResponse("Bond Estimate demo view is working ✅")
