from django.contrib import admin
from apps.bond_estimate.model.CapitalDetailsModel import CapitalDetails
from apps.bond_estimate.model.BondEstimationApplicationModel import BondEstimationApplication

admin.site.register(CapitalDetails)
admin.site.register(BondEstimationApplication)