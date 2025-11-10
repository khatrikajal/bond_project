from rest_framework import serializers

class BankDocumentExtractSerializer(serializers.Serializer):
    document_type = serializers.ChoiceField(choices=["cheque", "bank_statement", "passbook"])
    file = serializers.FileField()
