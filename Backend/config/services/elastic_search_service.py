# G:\bond_platform\Backend\config\services\elastic_search_service.py
from elasticsearch import Elasticsearch
from django.conf import settings

class ElasticService:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = Elasticsearch(
                hosts=[settings.ELASTICSEARCH_DSL['default']['hosts']],
                basic_auth=settings.ELASTICSEARCH_DSL['default']['basic_auth'],
                verify_certs=settings.ELASTICSEARCH_DSL['default'].get('verify_certs', True)
            )
        return cls._client

    
    @classmethod
    def index_document(cls, index_name, doc_id, body):
        cls.get_client().index(index=index_name, id=doc_id, body=body)

    @classmethod
    def delete_document(cls, index_name, doc_id):
        cls.get_client().delete(index=index_name, id=doc_id, ignore=[404])

    @classmethod
    def search(cls, index_name, query):
        return cls.get_client().search(index=index_name, body=query)
