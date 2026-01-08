from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0002_customer_loyalty_points"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="weight_grams",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
