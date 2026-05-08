from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Invitation, ListMember, Notification, Product, ShoppingList
from .serializers import (
    InvitationSerializer,
    NotificationSerializer,
    ProductSerializer,
    ProductWriteSerializer,
    ShoppingListSerializer,
)
from .services import notify_list_members


def get_accessible_list_or_404(list_id: int, user) -> ShoppingList:
    return get_object_or_404(
        ShoppingList.objects.filter(memberships__user=user).distinct(),
        id=list_id,
    )


def ensure_owner(shopping_list: ShoppingList, user) -> None:
    is_owner = shopping_list.memberships.filter(user=user, role=ListMember.Role.OWNER).exists()
    if not is_owner:
        raise PermissionDenied("Действие доступно только владельцу списка.")


class ShoppingListViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingListSerializer

    def get_queryset(self):
        return (
            ShoppingList.objects.filter(memberships__user=self.request.user)
            .select_related("owner")
            .annotate(members_count=Count("memberships", distinct=True))
            .distinct()
        )

    def perform_create(self, serializer):
        shopping_list = serializer.save(owner=self.request.user)
        ListMember.objects.create(
            shopping_list=shopping_list,
            user=self.request.user,
            role=ListMember.Role.OWNER,
        )

    def destroy(self, request, *args, **kwargs):
        shopping_list = self.get_object()
        ensure_owner(shopping_list, request.user)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=("post",), url_path="invite")
    def invite(self, request, pk=None):
        shopping_list = self.get_object()
        ensure_owner(shopping_list, request.user)
        invitation = Invitation.objects.create(
            shopping_list=shopping_list,
            created_by=request.user,
        )
        return Response(InvitationSerializer(invitation, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("get",), url_path="members")
    def members(self, request, pk=None):
        shopping_list = self.get_object()
        members = shopping_list.memberships.select_related("user").order_by("joined_at")
        data = [
            {
                "user_id": member.user_id,
                "email": member.user.email,
                "username": member.user.username,
                "role": member.role,
                "joined_at": member.joined_at,
            }
            for member in members
        ]
        return Response(data)


class ProductListCreateAPIView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductWriteSerializer
        return ProductSerializer

    def get_shopping_list(self) -> ShoppingList:
        return get_accessible_list_or_404(self.kwargs["list_id"], self.request.user)

    def get_queryset(self):
        shopping_list = self.get_shopping_list()
        show_bought = self.request.query_params.get("bought") == "1"
        return (
            Product.objects.filter(shopping_list=shopping_list, is_bought=show_bought)
            .select_related("category", "added_by", "bought_by")
            .order_by("is_bought", "-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["shopping_list"] = self.get_shopping_list()
        return context

    def create(self, request, *args, **kwargs):
        shopping_list = self.get_shopping_list()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        notify_list_members(
            shopping_list=shopping_list,
            actor=request.user,
            event_type=Notification.Type.PRODUCT_ADDED,
            message=f"{request.user.email} добавил(а) товар: {product.name}",
            product=product,
        )
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = "product_id"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return ProductWriteSerializer
        return ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(shopping_list__memberships__user=self.request.user).select_related(
            "shopping_list", "category", "added_by", "bought_by"
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        notify_list_members(
            shopping_list=product.shopping_list,
            actor=request.user,
            event_type=Notification.Type.PRODUCT_UPDATED,
            message=f"{request.user.email} изменил(а) товар: {product.name}",
            product=product,
        )
        return Response(ProductSerializer(product).data)

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        shopping_list = product.shopping_list
        product_name = product.name
        self.perform_destroy(product)
        notify_list_members(
            shopping_list=shopping_list,
            actor=request.user,
            event_type=Notification.Type.PRODUCT_DELETED,
            message=f"{request.user.email} удалил(а) товар: {product_name}",
            product=None,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductBuyAPIView(generics.GenericAPIView):
    serializer_class = ProductSerializer
    lookup_url_kwarg = "product_id"

    def get_queryset(self):
        return Product.objects.filter(shopping_list__memberships__user=self.request.user).select_related(
            "shopping_list", "category", "added_by", "bought_by"
        )

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(self.get_queryset(), id=kwargs["product_id"])
        if product.is_bought:
            return Response(ProductSerializer(product).data)
        product.mark_as_bought(request.user)
        notify_list_members(
            shopping_list=product.shopping_list,
            actor=request.user,
            event_type=Notification.Type.PRODUCT_BOUGHT,
            message=f"{request.user.email} купил(а): {product.name}",
            product=product,
        )
        return Response(ProductSerializer(product).data)


class HistoryAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        shopping_list = get_accessible_list_or_404(self.kwargs["list_id"], self.request.user)
        return Product.objects.filter(shopping_list=shopping_list, is_bought=True).select_related(
            "category", "added_by", "bought_by"
        )


class AcceptInvitationAPIView(generics.GenericAPIView):
    serializer_class = InvitationSerializer

    def post(self, request, *args, **kwargs):
        invitation = get_object_or_404(Invitation.objects.select_related("shopping_list"), code=kwargs["code"])
        if not invitation.is_active or invitation.is_expired:
            raise ValidationError("Приглашение недействительно или истекло.")

        membership, created = ListMember.objects.get_or_create(
            shopping_list=invitation.shopping_list,
            user=request.user,
            defaults={"role": ListMember.Role.MEMBER},
        )
        if created:
            notify_list_members(
                shopping_list=invitation.shopping_list,
                actor=request.user,
                event_type=Notification.Type.MEMBER_JOINED,
                message=f"{request.user.email} присоединился(лась) к списку: {invitation.shopping_list.name}",
            )
        return Response(
            {
                "status": "joined" if created else "already_member",
                "list_id": invitation.shopping_list_id,
                "role": membership.role,
            }
        )


class NotificationListAPIView(mixins.ListModelMixin, generics.GenericAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related("shopping_list", "product")

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        qs = self.get_queryset()
        if ids:
            qs = qs.filter(id__in=ids)
        updated = qs.update(is_read=True)
        return Response({"updated": updated})
