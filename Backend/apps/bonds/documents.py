# C:\Users\Admin\Desktop\bond_platform\bonds\documents.py
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import ISINBasicInfo

@registry.register_document
class ISINBasicInfoDocument(Document):
    class Index:
        name = 'bonds'

    class Django:
        model = ISINBasicInfo
        fields = [
            'isin_code',
            'issuer_name',
            'security_type',
        ]
