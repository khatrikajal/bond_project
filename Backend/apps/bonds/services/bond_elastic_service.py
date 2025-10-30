from config.services.elastic_search_service import ElasticService

class BondElasticService(ElasticService):
    INDEX = "bonds"

    @classmethod
    def index_bond(cls, bond_obj):
        doc = {
            "isin_code": bond_obj.isin_code,
            "issuer_name": bond_obj.issuer_name,
            "security_type": bond_obj.security_type,
            "ytm_percent": float(bond_obj.ytm_percent or 0),
            "maturity_date": bond_obj.maturity_date.isoformat() if bond_obj.maturity_date else None,
            "coupon_rate_percent": float(bond_obj.coupon_rate_percent or 0),
            "face_value_rs": float(bond_obj.face_value_rs or 0),
            "listed_unlisted": bond_obj.listed_unlisted,
            "trading_status": bond_obj.trading_status,
            "tax_category": bond_obj.tax_category,
            "secured": bond_obj.secured,
            "primary_exchange": bond_obj.primary_exchange,
            "series": bond_obj.series,
        }
        cls.index_document(cls.INDEX, bond_obj.isin_code, doc)

    @classmethod
    def delete_bond(cls, isin_code):
        cls.delete_document(cls.INDEX, isin_code)

    @classmethod
    def search_bonds(cls, issuer_name=None, security_type=None, size=20):
        query = {"query": {"bool": {"must": []}}}
        if issuer_name:
            query["query"]["bool"]["must"].append({"match": {"issuer_name": issuer_name}})
        if security_type:
            query["query"]["bool"]["must"].append({"match": {"security_type": security_type}})
        return cls.search(cls.INDEX, query, size=size)

        