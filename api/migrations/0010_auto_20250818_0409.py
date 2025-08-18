from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_tituladoshistoricos_semestre'),  # Este ya es el correcto, NO lo cambies
    ]

    operations = [
        migrations.AddField(
            model_name='tituladoshistoricos',
            name='semestre',
            field=models.IntegerField(choices=[(5, 'TSU'), (10, 'Ingeniería')], default=5),
        ),
    ]
