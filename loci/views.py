from django.shortcuts import render

# Create your views here.
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics

from accounts.roles import get_role, LIMITED, LIMITED_REGION_IDS
from .filters import LocusFilter
from .models import Locus, LocusMember
from .pagination import LocusPagination
from .permissions import LocusAccessPermission
from .serializers import LocusSerializer, LocusWithMembersSerializer

SIDELOAD_MEMBERS = 'locusMembers'

class LocusListView(generics.ListAPIView):
    permission_classes = [LocusAccessPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LocusFilter
    pagination_class = LocusPagination

    def _sideload(self):
        return self.request.query_params.get('sideloading') == SIDELOAD_MEMBERS

    def get_serializer_class(self):
        return LocusWithMembersSerializer if self._sideload() else LocusSerializer

    def get_queryset(self):
        qs = Locus.objects.order_by('id')
        is_limited = get_role(self.request.user) == LIMITED
        if is_limited:
            qs = qs.filter(members__region_id__in=LIMITED_REGION_IDS).distinct()
        if self._sideload():
            members = LocusMember.objects.all()
            if is_limited:
                members = members.filter(region_id__in=LIMITED_REGION_IDS)
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
