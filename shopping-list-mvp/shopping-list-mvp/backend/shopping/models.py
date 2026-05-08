import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class ShoppingList(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_shopping_lists")
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return self.name


class ListMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Владелец"
        MEMBER = "MEMBER", "Участник"

    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopping_memberships")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("shopping_list", "user"), name="uniq_list_member"),
        ]
        ordering = ("joined_at",)

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.shopping_list_id} ({self.role})"


class Category(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("shopping_list", "name"), name="uniq_category_per_list"),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    name = models.CharField(max_length=160)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=32, blank=True, default="шт")
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comment = models.TextField(blank=True, default="")
    is_bought = models.BooleanField(default=False)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="added_products")
    bought_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="bought_products")
    bought_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("is_bought", "-created_at")
        indexes = [
            models.Index(fields=("shopping_list", "is_bought")),
        ]

    def mark_as_bought(self, user) -> None:
        self.is_bought = True
        self.bought_by = user
        self.bought_at = timezone.now()
        self.save(update_fields=("is_bought", "bought_by", "bought_at", "updated_at"))

    def __str__(self) -> str:
        return self.name


class Invitation(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="invitations")
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_invitations")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    @property
    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at <= timezone.now())

    def __str__(self) -> str:
        return str(self.code)


class Notification(models.Model):
    class Type(models.TextChoices):
        PRODUCT_ADDED = "PRODUCT_ADDED", "Товар добавлен"
        PRODUCT_UPDATED = "PRODUCT_UPDATED", "Товар изменён"
        PRODUCT_DELETED = "PRODUCT_DELETED", "Товар удалён"
        PRODUCT_BOUGHT = "PRODUCT_BOUGHT", "Товар куплен"
        MEMBER_JOINED = "MEMBER_JOINED", "Участник присоединился"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="notifications")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications")
    type = models.CharField(max_length=32, choices=Type.choices)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.message
