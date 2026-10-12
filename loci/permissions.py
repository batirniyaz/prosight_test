from rest_framework.permissions import BasePermission
from accounts.roles import get_role, ROLES, NORMAL, LIMITED, LIMITED_REGION_IDS
from .models import Locus, LocusMember


class LocusAccessPermission(BasePermission):
    def has_permission(self, request, view):
        role = get_role(request.user)
        if role not in ROLES:
            self.message = 'User has no role.'
            return False
        if role == NORMAL and request.query_params.get('sideloading'):
            self.message = 'Sideloading is not allowed for this user.'
            return False
        return True


def visible_members(user):
    members = LocusMember.objects.all()
    if get_role(user) == LIMITED:
        members = members.filter(region_id__in=LIMITED_REGION_IDS)
    return members


def visible_loci(user):
    loci = Locus.objects.all()
    if get_role(user) == LIMITED:
        loci = loci.filter(id__in=visible_members(user).values("locus_id"))
    return loci
