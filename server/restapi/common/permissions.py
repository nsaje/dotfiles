from rest_framework import permissions


class CanSetBidModifiersPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.can_set_bid_modifiers"))
