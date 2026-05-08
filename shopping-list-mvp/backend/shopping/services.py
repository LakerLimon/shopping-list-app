from django.db.models import QuerySet

from .models import Notification, ShoppingList


def notify_list_members(*, shopping_list: ShoppingList, actor, event_type: str, message: str, product=None) -> None:
    """Creates internal MVP notifications for all list members except the actor."""
    users: QuerySet = shopping_list.memberships.select_related("user").exclude(user=actor)
    notifications = [
        Notification(
            user=membership.user,
            shopping_list=shopping_list,
            product=product,
            type=event_type,
            message=message,
        )
        for membership in users
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)
