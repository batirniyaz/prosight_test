import django_filters as filters
from django_filters.constants import EMPTY_VALUES

from .models import Locus
from .permissions import visible_members


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class StableOrderingFilter(filters.OrderingFilter):

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        ordering = [self.get_ordering_value(param) for param in value if param not in EMPTY_VALUES]
        if "id" not in ordering and "-id" not in ordering:
            ordering.append("id")
        return qs.order_by(*ordering)


class LocusFilter(filters.FilterSet):
    id = NumberInFilter(field_name="id")
    assemblyId = filters.CharFilter(field_name="assembly_id")
    regionId = NumberInFilter(field_name="region_id", method="filter_members")
    membershipStatus = filters.CharFilter(field_name="membership_status", method="filter_members")
    sort = StableOrderingFilter(fields=(
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

    def filter_members(self, queryset, name, value):
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        member_lookups = {
            f"{f.field_name}__{f.lookup_expr}": self.form.cleaned_data[name]
            for name, f in self.filters.items()
            if f.method == "filter_members" and self.form.cleaned_data.get(name) not in EMPTY_VALUES
        }
        if member_lookups:
            members = visible_members(self.request.user).filter(**member_lookups)
            queryset = queryset.filter(id__in=members.values("locus_id"))
        return queryset
