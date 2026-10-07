import django_filters as filters
from .models import Locus


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class LocusFilter(filters.FilterSet):
    id = NumberInFilter(field_name="id")
    assembly_id = filters.CharFilter(field_name="assembly_id")
    regionId = NumberInFilter(field_name="members__region_id", distinct=True)
    membershipStatus = filters.CharFilter(field_name="members__membership_status", distinct=True)
    sort = filters.OrderingFilter(fields=(
        ('id', 'id'),
        ('assembly_id', 'assembly_id'),
        ('locus_start', 'locus_start'),
        ('locus_stop', 'locus_stop'),
        ('member_count', 'member_count'),
    ))

    class Meta:
        model = Locus
        fields = []