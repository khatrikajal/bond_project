from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from ..models.CompanyDocumentModel import CompanyDocument
from ..models.CompanyInformationModel import CompanyInformation
from ..models.CompanyOnboardingApplicationModel import CompanyOnboardingApplication


class CompanyOwnershipMixin:
    """
    Mixin to verify user owns the company and get company instance.
    Prevents N+1 queries with select_related.
    """

    def get_company_for_user(self, company_id, user):
        from ..models.CompanyInformationModel import CompanyInformation

        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication required")

        try:
            company = CompanyInformation.objects.select_related(
                'user',
                'application'
            ).get(
                company_id=company_id,
                del_flag=0
            )

            if company.user_id != user.user_id:
                raise PermissionDenied("You do not have permission to access this company's documents")

            return company

        except CompanyInformation.DoesNotExist:
            raise NotFound("Company not found")


class DocumentQueryOptimizationMixin:
    """
    Mixin for optimized document queries to avoid N+1 problems.
    """

    def get_documents_for_company(self, company_id):
        return CompanyDocument.objects.select_related(
            'company',
            'user_id_updated_by'
        ).filter(
            company_id=company_id,
            del_flag=0
        )

    def get_optimized_documents_queryset(self, company_id):
        """Alias method for consistency"""
        return self.get_documents_for_company(company_id)

    def get_document_with_company(self, document_id, company_id):
        try:
            return CompanyDocument.objects.select_related(
                'company',
                'user_id_updated_by'
            ).get(
                document_id=document_id,
                company_id=company_id,
                del_flag=0
            )
        except CompanyDocument.DoesNotExist:
            raise NotFound("Document not found")


class DocumentValidationMixin:
    """
    Common file validation for Company Documents.
    """

    allowed_content_types = ['application/pdf', 'image/jpeg', 'image/png']
    max_size_mb = 5

    def validate_file_type(self, file):
        if file.content_type not in self.allowed_content_types:
            raise ValidationError("Invalid file type. Allowed: PDF, JPEG, PNG")

    def validate_file_size(self, file):
        max_bytes = self.max_size_mb * 1024 * 1024
        if file.size > max_bytes:
            raise ValidationError(f"File size exceeds {self.max_size_mb}MB limit")


class ApplicationStepUpdateMixin:
    """
    Mixin to handle step updates for CompanyOnboardingApplication.
    """

    def get_application_for_company(self, company):
        if not hasattr(company, 'application') or not company.application:
            raise ValidationError("No onboarding application found for this company")
        return company.application

    def check_mandatory_documents_uploaded(self, company_id):
        return CompanyDocument.check_company_documents_complete(company_id)

    def update_document_step(self, company, record_ids=None):
        """
        Update step 3 (documents) based on current document status.
        This is the method that views should call.
        """
        if not hasattr(company, 'application') or not company.application:
            return
        
        application = company.application
        all_mandatory_uploaded = self.check_mandatory_documents_uploaded(company.company_id)
        
        # Get all document IDs if not provided
        if record_ids is None:
            document_ids = list(
                CompanyDocument.objects.filter(
                    company_id=company.company_id,
                    del_flag=0
                ).values_list('document_id', flat=True)
            )
            record_ids = [str(doc_id) for doc_id in document_ids]
        
        application.update_state(
            step_number=3,
            completed=all_mandatory_uploaded,
            record_ids=record_ids
        )

    def update_application_step(self, company, step_number, record_ids=None, completed=True, reason=None):
        """
        Generic method to update any step.
        For document step (4), use update_document_step() instead.
        """
        application = self.get_application_for_company(company)
        
        try:
            application.update_state(
                step_number=step_number,
                completed=completed,
                record_ids=record_ids or [],
            )
        except Exception as e:
            raise ValidationError(f"Failed to update application step: {str(e)}")

    def mark_step_complete_if_ready(self, company, step_number, record_ids=None):
        all_uploaded = self.check_mandatory_documents_uploaded(company.company_id)
        if all_uploaded:
            self.update_application_step(company, step_number=step_number, record_ids=record_ids)


class SoftDeleteMixin(ApplicationStepUpdateMixin):
    """
    Handles soft delete and restore for Company Documents with application step updates.
    """

    def soft_delete_document(self, document, user, step_number=4):
        document.del_flag = 1
        if user and user.is_authenticated:
            document.user_id_updated_by = user
        document.save(update_fields=['del_flag', 'user_id_updated_by', 'updated_at'])

        company = document.company
        self.update_document_step(company)

        return not self.check_mandatory_documents_uploaded(company.company_id)

    def restore_document(self, document, user, step_number=4):
        document.del_flag = 0
        if user and user.is_authenticated:
            document.user_id_updated_by = user
        document.save(update_fields=['del_flag', 'user_id_updated_by', 'updated_at'])

        company = document.company
        self.update_document_step(company)