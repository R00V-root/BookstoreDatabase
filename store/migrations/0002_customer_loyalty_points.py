from __future__ import annotations

from django.db import migrations, models


def add_loyalty_points_column(apps, schema_editor):
    customer_model = apps.get_model("store", "Customer")
    table_name = customer_model._meta.db_table
    column_name = "loyalty_points"

    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )
        }

    if column_name in existing_columns:
        return

    field = models.PositiveIntegerField(default=0)
    field.set_attributes_from_name(column_name)
    definition, params = schema_editor.column_sql(customer_model, field)
    if definition is None:
        return

    quoted_table = schema_editor.quote_name(table_name)
    quoted_column = schema_editor.quote_name(field.column)
    sql = f"ALTER TABLE {quoted_table} ADD COLUMN {quoted_column} {definition}"
    schema_editor.execute(sql, params)


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_loyalty_points_column, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="customer",
                    name="loyalty_points",
                    field=models.PositiveIntegerField(default=0),
                ),
            ],
        ),
    ]
