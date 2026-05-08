from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Invitation, ListMember, Notification, Product, ShoppingList

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "username")


class ShoppingListSerializer(serializers.ModelSerializer):
    owner = UserBriefSerializer(read_only=True)
    role = serializers.SerializerMethodField()
    members_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ShoppingList
        fields = ("id", "name", "owner", "role", "members_count", "created_at", "updated_at")
        read_only_fields = ("id", "owner", "role", "members_count", "created_at", "updated_at")

    def get_role(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        membership = obj.memberships.filter(user=request.user).first()
        return membership.role if membership else None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")


class ProductSerializer(serializers.ModelSerializer):
    added_by = UserBriefSerializer(read_only=True)
    bought_by = UserBriefSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "shopping_list",
            "name",
            "quantity",
            "unit",
            "estimated_price",
            "category",
            "comment",
            "is_bought",
            "added_by",
            "bought_by",
            "bought_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "shopping_list",
            "is_bought",
            "added_by",
            "bought_by",
            "bought_at",
            "created_at",
            "updated_at",
        )


class ProductWriteSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(required=False, allow_blank=True, max_length=64, write_only=True)

    class Meta:
        model = Product
        fields = ("name", "quantity", "unit", "estimated_price", "category_name", "comment")

    def _resolve_category(self, shopping_list, category_name):
        if not category_name:
            return None
        category, _ = Category.objects.get_or_create(
            shopping_list=shopping_list,
            name=category_name.strip(),
        )
        return category

    def create(self, validated_data):
        shopping_list = self.context["shopping_list"]
        user = self.context["request"].user
        category_name = validated_data.pop("category_name", "")
        product = Product.objects.create(
            shopping_list=shopping_list,
            added_by=user,
            category=self._resolve_category(shopping_list, category_name),
            **validated_data,
        )
        return product

    def update(self, instance, validated_data):
        category_name = validated_data.pop("category_name", None)
        if category_name is not None:
            instance.category = self._resolve_category(instance.shopping_list, category_name)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class InvitationSerializer(serializers.ModelSerializer):
    invite_url = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = ("code", "invite_url", "is_active", "created_at", "expires_at")
        read_only_fields = fields

    def get_invite_url(self, obj):
        request = self.context.get("request")
        path = f"/invite/{obj.code}/"
        if request:
            return request.build_absolute_uri(path)
        return path


class NotificationSerializer(serializers.ModelSerializer):
    shopping_list_name = serializers.CharField(source="shopping_list.name", read_only=True)

    class Meta:
        model = Notification
        fields = ("id", "type", "message", "shopping_list", "shopping_list_name", "product", "is_read", "created_at")
        read_only_fields = fields
