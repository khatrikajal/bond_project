from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('issuer_kyc', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='companyonboardingapplication',
            index=models.Index(fields=['last_accessed_step'], name='company_onb_last_ac_4eecd1_idx'),
        ),
    ]
