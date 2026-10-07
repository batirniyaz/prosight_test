from rest_framework import serializers
from .models import Locus, LocusMember

class LocusMemberSerializer(serializers.ModelSerializer):
    locusMemberId = serializers.IntegerField(source="id")
    ursTaxid = serializers.CharField(source="urs_taxid")
    regionId = serializers.IntegerField(source="region_id")
    membershipStatus = serializers.CharField(source="membership_status")

    class Meta:
        model = LocusMember
        fields = ['locusMemberId', 'ursTaxid', 'regionId', 'membershipStatus']


class LocusSerializer(serializers.ModelSerializer):
    assemblyId = serializers.CharField(source="assembly_id")
    locusName = serializers.CharField(source="locus_name")
    publicLocusName = serializers.CharField(source="public_locus_name")
    locusStart = serializers.IntegerField(source="locus_start")
    locusStop = serializers.IntegerField(source="locus_stop")
    memberCount = serializers.IntegerField(source="member_count")

    class Meta:
        model = Locus
        fields = ['id', 'assemblyId', 'locusName', 'publicLocusName', 'chromosome', 'strand', 'locusStart', 'locusStop', 'memberCount']


class LocusWithMembersSerializer(LocusSerializer):
    locusMembers = LocusMemberSerializer(many=True, source="members")

    class Meta(LocusSerializer.Meta):
        fields = LocusSerializer.Meta.fields + ['locusMembers']
