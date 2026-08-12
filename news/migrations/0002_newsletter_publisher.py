# Generated for the capstone newsletter publisher relationship.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("news", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="newsletter",
            name="publisher",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="newsletters",
                to="news.publisher",
            ),
        ),
        migrations.AlterField(
            model_name="newsletter",
            name="articles",
            field=models.ManyToManyField(
                blank=True,
                related_name="newsletters",
                to="news.article",
            ),
        ),
    ]
