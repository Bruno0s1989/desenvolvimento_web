# Generated by Django 5.1.7 on 2025-04-02 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mentorados', '0002_disponibilidadehorarios_reuniao'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentorados',
            name='token',
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
    ]
