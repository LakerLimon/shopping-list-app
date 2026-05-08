from django.contrib import admin

from .models import Category, Invitation, ListMember, Notification, Product, ShoppingList


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "created_at", "updated_at")
    search_fields = ("name", "owner__email")


@admin.register(ListMember)
class ListMemberAdmin(admin.ModelAdmin):
    list_display = ("shopping_list", "user", "role", "joined_at")
    list_filter = ("role",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "shopping_list")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "shopping_list", "quantity", "unit", "is_bought", "added_by", "bought_by")
    list_filter = ("is_bought", "category")
    search_fields = ("name", "comment")


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("code", "shopping_list", "created_by", "is_active", "created_at", "expires_at")
    list_filter = ("is_active",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "shopping_list", "type", "message", "is_read", "created_at")
    list_filter = ("type", "is_read")
