
# Create your views here.
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from .filters import LocusFilter
from .pagination import LocusPagination
from .permissions import LocusAccessPermission, visible_loci, visible_members
from .serializers import LocusSerializer, LocusWithMembersSerializer

SIDELOAD_MEMBERS = 'locusMembers'

class LocusListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, LocusAccessPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LocusFilter
    pagination_class = LocusPagination

    def _sideload(self):
        value = self.request.query_params.get('sideloading')
        if not value:
            return False
        if value != SIDELOAD_MEMBERS:
            raise ValidationError({'sideloading': [f'Unknown value "{value}". Allowed: {SIDELOAD_MEMBERS}.']})
        return True

    def get_serializer_class(self):
        return LocusWithMembersSerializer if self._sideload() else LocusSerializer

    def get_queryset(self):
        qs = visible_loci(self.request.user).order_by('id')
        if self._sideload():
            members = visible_members(self.request.user).order_by('id')
            qs = qs.prefetch_related(Prefetch("members", queryset=members))
        return qs

    @extend_schema(parameters=[
        OpenApiParameter(
            name='sideloading',
            description='Sideloading parameter',
            required=False,
            type=str,
            enum=[SIDELOAD_MEMBERS],
        )])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
