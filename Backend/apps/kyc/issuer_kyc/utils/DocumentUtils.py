"""
Utility classes for document operations.
Handles document status checking and response formatting with dropdown groups.
"""
import logging

logger = logging.getLogger(__name__)


class DocumentStatusChecker:
    """Utility class for checking document upload status"""

    @staticmethod
    def get_company_document_status(company_id):
        """
        Corrected version:
        ✅ Uses document_name to detect mandatory documents
        ✅ No dependency on is_mandatory flag
        ✅ Always correct counts
        """

        from ..models.CompanyDocumentModel import CompanyDocument

        logger.debug(f"[STATUS] Checking document status for company_id={company_id}")

        try:
            # ✅ Fetch all uploaded docs
            docs = CompanyDocument.objects.filter(
                company_id=company_id,
                del_flag=0
            )

            mandatory_list = CompanyDocument.MANDATORY_DOCUMENTS
            optional_list = CompanyDocument.get_optional_documents()

            uploaded_mandatory = []
            uploaded_optional = []

            documents_list = []

            for d in docs:
                doc_info = {
                    "document_id": str(d.document_id),
                    "document_name": d.document_name,
                    "document_name_display": d.get_document_name_display(),
                    "document_type": d.document_type,
                    "file_size": d.file_size,
                    "uploaded_at": d.uploaded_at.isoformat(),
                    "file_path": d.document_file.name if d.document_file else None,
                    "is_verified": d.is_verified,
                    "mandatory": d.document_name in mandatory_list,
                }

                documents_list.append(doc_info)

                # ✅ Correct Mandatory Logic
                if d.document_name in mandatory_list:
                    uploaded_mandatory.append(doc_info)
                else:
                    uploaded_optional.append(doc_info)

            # ✅ Correct missing mandatory logic
            uploaded_names = [d.document_name for d in docs]

            missing = [
                doc_name for doc_name in mandatory_list
                if doc_name not in uploaded_names
            ]

            # ✅ Missing mandatory with display labels
            missing_mandatory_display = [
                {
                    "document_name": name,
                    "document_name_display":
                        dict(CompanyDocument.DOCUMENT_NAMES).get(name, name)
                }
                for name in missing
            ]

            step_completed = len(missing) == 0

            # ✅ Dropdown groups
            document_groups = {
                "moa_aoa_group": {
                    "options": [
                        {"value": "MOA", "label": "Memorandum of Association (MoA)"},
                        {"value": "AOA", "label": "Articles of Association (AoA)"}
                    ],
                    "uploaded": None,
                    "is_optional": True
                },
                "msme_udyam_group": {
                    "options": [
                        {"value": "MSME", "label": "MSME Certificate"},
                        {"value": "UDYAM", "label": "Udyam Certificate"}
                    ],
                    "uploaded": None,
                    "is_optional": True
                }
            }

            for d in uploaded_optional:
                if d["document_name"] in CompanyDocument.MOA_AOA_GROUP:
                    document_groups["moa_aoa_group"]["uploaded"] = d

                if d["document_name"] in CompanyDocument.MSME_UDYAM_GROUP:
                    document_groups["msme_udyam_group"]["uploaded"] = d

            status = {
                "total_documents": len(docs),
                "mandatory_documents": len(mandatory_list),
                "optional_documents": len(optional_list),

                "uploaded_mandatory": len(uploaded_mandatory),
                "uploaded_optional": len(uploaded_optional),

                "all_mandatory_uploaded": step_completed,
                "missing_mandatory_documents": missing_mandatory_display,

                "uploaded_documents": documents_list,
                "document_groups": document_groups
            }

            logger.info(
                f"[STATUS] company_id={company_id} | "
                f"mandatory={len(uploaded_mandatory)}/{len(mandatory_list)} | "
                f"step_completed={step_completed}"
            )

            return status

        except Exception as e:
            logger.error(
                f"[STATUS] Error while calculating status for company_id={company_id}: {str(e)}",
                exc_info=True
            )

            # Safe fallback
            return {
                "total_documents": 0,
                "mandatory_documents": len(CompanyDocument.MANDATORY_DOCUMENTS),
                "optional_documents": len(CompanyDocument.get_optional_documents()),
                "uploaded_mandatory": 0,
                "uploaded_optional": 0,
                "all_mandatory_uploaded": False,
                "missing_mandatory_documents": [],
                "uploaded_documents": [],
                "document_groups": {}
            }


class DocumentResponseFormatter:
    """Utility class for formatting API responses"""

    @staticmethod
    def format_success_response(document, message="Document uploaded successfully"):
        try:
            return {
                "success": True,
                "message": message,
                "data": {
                    "document_id": str(document.document_id),
                    "document_name": document.document_name,
                    "document_name_display": document.get_document_name_display(),
                    "document_type": document.document_type,
                    "file_size": document.file_size,
                    "file_path": document.document_file.name if document.document_file else None,
                    "uploaded_at": document.uploaded_at.isoformat(),
                    "is_verified": document.is_verified,
                    "is_mandatory": document.document_name in document.MANDATORY_DOCUMENTS,
                }
            }
        except Exception:
            return {"success": True, "message": message, "data": {}}

    @staticmethod
    def format_error_response(message, errors=None):
        return {
            "success": False,
            "message": message,
            **({"errors": errors} if errors else {})
        }

    @staticmethod
    def format_list_response(documents, status):
        return {
            "success": True,
            "message": "Documents retrieved",
            "data": {
                "documents": documents,
                "summary": {
                    "mandatory_total": status.get("mandatory_documents"),
                    "mandatory_uploaded": status.get("uploaded_mandatory"),
                    "optional_total": status.get("optional_documents"),
                    "optional_uploaded": status.get("uploaded_optional"),
                    "step_completed": status.get("all_mandatory_uploaded"),
                }
            }
        }
