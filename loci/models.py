from django.db import models

# Create your models here.

from django.db import models

class Locus(models.Model):
    id = models.BigIntegerField(primary_key=True)
    assembly_id = models.CharField(max_length=255)
    locus_name = models.CharField(max_length=255)
    public_locus_name = models.CharField(max_length=255)
    chromosome = models.CharField(max_length=255)
    strand = models.CharField(max_length=10)
    locus_start = models.IntegerField()
    locus_stop = models.IntegerField()
    member_count = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'rnc_locus'


class LocusMember(models.Model):
    id = models.BigIntegerField(primary_key=True)
    locus = models.ForeignKey(Locus, on_delete=models.DO_NOTHING, db_column='locus_id', related_name='members')
    urs_taxid = models.CharField(max_length=255)
    region_id = models.IntegerField()
    membership_status = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'rnc_locus_member'