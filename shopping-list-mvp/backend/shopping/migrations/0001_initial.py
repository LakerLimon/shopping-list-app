# Generated manually for the MVP archive.
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ShoppingList",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="owned_shopping_lists", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-updated_at",)},
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64)),
                ("shopping_list", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="categories", to="shopping.shoppinglist")),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Invitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="created_invitations", to=settings.AUTH_USER_MODEL)),
                ("shopping_list", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="shopping.shoppinglist")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="ListMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("OWNER", "Владелец"), ("MEMBER", "Участник")], default="MEMBER", max_length=16)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("shopping_list", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="shopping.shoppinglist")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shopping_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("joined_at",)},
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("quantity", models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                ("unit", models.CharField(blank=True, default="шт", max_length=32)),
                ("estimated_price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("comment", models.TextField(blank=True, default="")),
                ("is_bought", models.BooleanField(default=False)),
                ("bought_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("added_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="added_products", to=settings.AUTH_USER_MODEL)),
                ("bought_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bought_products", to=settings.AUTH_USER_MODEL)),
                ("category", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="products", to="shopping.category")),
                ("shopping_list", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="products", to="shopping.shoppinglist")),
            ],
            options={"ordering": ("is_bought", "-created_at")},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("PRODUCT_ADDED", "Товар добавлен"), ("PRODUCT_UPDATED", "Товар изменён"), ("PRODUCT_DELETED", "Товар удалён"), ("PRODUCT_BOUGHT", "Товар куплен"), ("MEMBER_JOINED", "Участник присоединился")], max_length=32)),
                ("message", models.CharField(max_length=255)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notifications", to="shopping.product")),
                ("shopping_list", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="shopping.shoppinglist")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(fields=("shopping_list", "name"), name="uniq_category_per_list"),
        ),
        migrations.AddConstraint(
            model_name="listmember",
            constraint=models.UniqueConstraint(fields=("shopping_list", "user"), name="uniq_list_member"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["shopping_list", "is_bought"], name="shopping_pr_shoppin_36d498_idx"),
        ),
    ]
