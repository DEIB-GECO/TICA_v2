# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals
from django.db import models
from django import forms

MAX_DISTANCES = ((1100, '1100bp'),
                 (2200, '2200bp'),
                 (5500, '5500bp')
                 )

TESTS = (('average', 'Average'),
         ('mad', 'Median Absolute Deviation'),
         ('median', 'Median'),
         ('tail_1000', 'Right tail size'))

P_VALUES = ((5, '0.05'),
            (10, '0.1'),
            (20, '0.2')
            )

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
    cumulative_count_tss = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'hepg2'
        unique_together = (('tf1', 'tf2', 'distance'),)

    def __str__(self):
        return '%s_%s_%d_%d_%d_%d_%d' % (
            self.tf1, self.tf2, self.distance,self.count_all,self.count_tss,self.cumulative_count_all, self.cumulative_count_tss
        )


class Hepg2Null(models.Model):
    tf1 = models.CharField(primary_key=True, max_length=20)
    tf2 = models.CharField(max_length=20)
    max_distance = models.IntegerField()
    average = models.FloatField(blank=True, null=True)
    median = models.FloatField(blank=True, null=True)
    mad = models.FloatField(blank=True, null=True)
    tail_00 = models.FloatField(blank=True, null=True)
    tail_01 = models.FloatField(blank=True, null=True)
    tail_02 = models.FloatField(blank=True, null=True)
    tail_03 = models.FloatField(blank=True, null=True)
    tail_04 = models.FloatField(blank=True, null=True)
    tail_05 = models.FloatField(blank=True, null=True)
    tail_06 = models.FloatField(blank=True, null=True)
    tail_07 = models.FloatField(blank=True, null=True)
    tail_08 = models.FloatField(blank=True, null=True)
    tail_09 = models.FloatField(blank=True, null=True)
    tail_10 = models.FloatField(blank=True, null=True)
    tail_1000 = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'hepg2_null'
        unique_together = (('tf1', 'tf2', 'max_distance'),)

    def __str__(self):
        return ''


class Hepg2Temp(models.Model):
    tf1 = models.CharField(max_length=20)
    tf2 = models.CharField(max_length=20)
    dist = models.IntegerField()
    is_tss = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'hepg2_temp'


class EncodeFormModel(models.Model):
    cell = models.CharField(max_length=20)
    method = models.CharField(max_length=20)
    tf1 = models.CharField(max_length=20)
    max_dist = models.IntegerField(choices=MAX_DISTANCES, default=1)
    num_min = models.IntegerField()
    num_min_w_tsses = models.DecimalField(max_digits=5, decimal_places=2, blank=True)
    which_tests = models.CharField(max_length=20,choices=TESTS, blank=False, null=False, default=1)
    min_test_num = models.IntegerField()
    pvalue = models.IntegerField(choices=P_VALUES, default=1)
