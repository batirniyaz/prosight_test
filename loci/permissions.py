from rest_framework.permissions import BasePermission
from accounts.roles import get_role, NORMAL

class LocusAccessPermission(BasePermission):
    message = 'Sideloading is not allowed for this user.'

    def has_permission(self, request, view):
        if get_role(request.user) == NORMAL and request.query_params.get('sideloading'):
            return False
        return True