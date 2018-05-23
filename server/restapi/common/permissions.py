from rest_framework import permissions


class CanEditPublisherGroupsPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm('zemauth.can_edit_publisher_groups'))
