"""
Admin package for bond_estimate app.
Imports all admin configurations.
"""
from django.contrib import admin
# Example placeholder
# from apps.bond_estimate.model.bond import Bond
# @admin.register(Bond)
# class BondAdmin(admin.ModelAdmin):
#     pass


from apps.bond_estimate.admin import ganesh

from .BondEstimationApplicationAdmin import *
from .borrowing_admin import *
