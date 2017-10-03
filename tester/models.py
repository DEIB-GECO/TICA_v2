# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()
    
    class Meta:
        managed = False
        db_table = 'django_migrations'


class Hepg2(models.Model):
    tf1 = models.CharField(primary_key=True, max_length=20)
    tf2 = models.CharField(max_length=20)
    distance = models.IntegerField()
    count_all = models.IntegerField()
    count_tss = models.IntegerField()
    cumulative_count_all = models.IntegerField()
    
    def __str__(self):
        return 'Distance distribution for TFs: %s and %s' % (self.tf1,
                                                             self.tf2)
    
    class Meta:
        managed = False
        db_table = 'hepg2'
        unique_together = (('tf1', 'tf2', 'distance'),)


class Hepg2Null(models.Model):
    tf1 = models.CharField(primary_key=True, max_length=20)
    tf2 = models.CharField(max_length=20)
    max_distance = models.IntegerField()
    average = models.FloatField(blank=True, null=True)
    median = models.FloatField(blank=True, null=True)
    mad = models.FloatField(blank=True, null=True)
    tail_percentage_array = models.TextField(blank=True,
                                             null=True)  # This field type is a guess.
    
    def __str__(self):
        return 'Distribution statistics for TFs: %s ad %s, with maxdistance' \
               ' %d' % (self.tf1, self.tf2, self.max_distance)
    
    class Meta:
        managed = False
        db_table = 'hepg2_null'
        unique_together = (('tf1', 'tf2', 'max_distance'),)


class Hepg2Temp(models.Model):
    tf1 = models.CharField(max_length=20)
    tf2 = models.CharField(max_length=20)
    dist = models.IntegerField()
    is_tss = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'hepg2_temp'
