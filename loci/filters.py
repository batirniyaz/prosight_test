import django_filters as filters
from .models import Locus


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class LocusFilter(filters.FilterSet):
    id = NumberInFilter(field_name="id")
    assemblyId = filters.CharFilter(field_name="assembly_id")
    regionId = NumberInFilter(field_name="members__region_id", distinct=True)
    membershipStatus = filters.CharFilter(field_name="members__membership_status", distinct=True)
    sort = filters.OrderingFilter(fields=(
        ('id', 'id'),
        ('assembly_id', 'assemblyId'),
        ('locus_start', 'locusStart'),
        ('locus_stop', 'locusStop'),
        ('member_count', 'memberCount'),
        ('locus_name', 'locusName'),
        ('public_locus_name', 'publicLocusName'),
        ('chromosome', 'chromosome'),
        ('strand', 'strand'),
    ))

    class Meta:
        model = Locus
        fields = []