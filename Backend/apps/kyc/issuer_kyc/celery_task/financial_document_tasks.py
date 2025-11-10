from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from apps.kyc.issuer_kyc.models.FinancialDocumentModel import FinancialDocument
# from .services import DocumentVerificationService, RetryableVerificationService
import logging

logger = logging.getLogger(__name__)


# @shared_task(bind=True, max_retries=3, default_retry_delay=60)
# def verify_document_async(self, document_id):
#     """
#     Async task to verify a financial document
    
#     Args:
#         document_id: ID of the document to verify
    
#     Usage:
#         verify_document_async.delay(123)
#     """
    
#     try:
#         document = FinancialDocument.objects.get(document_id=document_id)
        
#         logger.info(f"Starting verification for document {document_id}")
        
#         # Perform verification
#         result = DocumentVerificationService.verify_document(document)
        
#         logger.info(f"Verification completed for document {document_id}: {result}")
        
#         return {
#             'success': True,
#             'document_id': document_id,
#             'is_verified': result['is_verified'],
#             'verification_source': result['verification_source']
#         }
    
#     except ObjectDoesNotExist:
#         logger.error(f"Document {document_id} not found")
#         return {
#             'success': False,
#             'error': 'Document not found'
#         }
    
#     except Exception as e:
#         logger.error(f"Verification failed for document {document_id}: {str(e)}")
        
#         # Retry the task
#         raise self.retry(exc=e)


# @shared_task
# def bulk_verify_documents(document_ids):
#     """
#     Verify multiple documents in bulk
    
#     Args:
#         document_ids: List of document IDs
    
#     Usage:
#         bulk_verify_documents.delay([1, 2, 3, 4, 5])
#     """
    
#     results = {
#         'total': len(document_ids),
#         'success': 0,
#         'failed': 0,
#         'details': []
#     }
    
#     for doc_id in document_ids:
#         try:
#             result = verify_document_async(doc_id)
            
#             if result.get('success'):
#                 results['success'] += 1
#             else:
#                 results['failed'] += 1
            
#             results['details'].append({
#                 'document_id': doc_id,
#                 'status': 'verified' if result.get('is_verified') else 'failed'
#             })
        
#         except Exception as e:
#             logger.error(f"Bulk verification failed for document {doc_id}: {str(e)}")
#             results['failed'] += 1
#             results['details'].append({
#                 'document_id': doc_id,
#                 'status': 'error',
#                 'error': str(e)
#             })
    
#     return results


# @shared_task
# def retry_failed_verifications():
#     """
#     Periodic task to retry failed verifications
    
#     Schedule in celery beat:
#     CELERY_BEAT_SCHEDULE = {
#         'retry-failed-verifications': {
#             'task': 'app.tasks.retry_failed_verifications',
#             'schedule': crontab(hour='*/2'),  # Every 2 hours
#         },
#     }
#     """
    
#     logger.info("Starting retry of failed verifications")
    
#     results = RetryableVerificationService.retry_failed_verifications(max_age_hours=24)
    
#     logger.info(f"Retry completed: {results}")
    
#     return results


# @shared_task
# def verify_company_documents(company_id, financial_year):
#     """
#     Verify all documents for a specific company and financial year
    
#     Args:
#         company_id: Company ID
#         financial_year: Financial year (e.g., 'FY2023-24')
    
#     Usage:
#         verify_company_documents.delay(123, 'FY2023-24')
#     """
    
#     documents = FinancialDocument.objects.filter(
#         company_id=company_id,
#         financial_year=financial_year,
#         is_verified=False,
#         is_del=0
#     ).values_list('document_id', flat=True)
    
#     document_ids = list(documents)
    
#     logger.info(f"Verifying {len(document_ids)} documents for company {company_id}")
    
#     return bulk_verify_documents(document_ids)


# @shared_task
# def cleanup_old_verification_logs(days=90):
#     """
#     Cleanup old verification logs
    
#     Args:
#         days: Delete logs older than this many days
    
#     Schedule in celery beat:
#     CELERY_BEAT_SCHEDULE = {
#         'cleanup-verification-logs': {
#             'task': 'app.tasks.cleanup_old_verification_logs',
#             'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
#         },
#     }
#     """
    
#     from datetime import timedelta
#     from django.utils import timezone
#     from .models import DocumentVerificationLog
    
#     cutoff_date = timezone.now() - timedelta(days=days)
    
#     deleted_count = DocumentVerificationLog.objects.filter(
#         verified_at__lt=cutoff_date
#     ).delete()[0]
    
#     logger.info(f"Cleaned up {deleted_count} old verification logs")
    
#     return {
#         'deleted_count': deleted_count,
#         'cutoff_date': str(cutoff_date)
#     }