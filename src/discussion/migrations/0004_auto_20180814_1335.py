# Generated by Django 2.0.7 on 2018-08-14 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discussion', '0003_auto_20170714_0744'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['-latest_modification']},
        ),
        migrations.AddField(
            model_name='notification',
            name='latest_modification',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
