# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models

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

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CellLineCouple(models.Model):
    cell_line = models.ForeignKey('CellLineTfs', models.DO_NOTHING, db_column='cell_line', primary_key=True)
    tf1 = models.CharField(max_length=20)
    tf2 = models.CharField(max_length=20)
    distance = models.IntegerField()
    count_all = models.IntegerField()
    count_tss = models.IntegerField()
    cumulative_count_all = models.IntegerField()
    cumulative_count_tss = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cell_line_couple'
        unique_together = (('cell_line', 'tf1', 'tf2', 'distance'),)


class CellLineNull(models.Model):
    cell_line = models.ForeignKey('CellLineTfs', models.DO_NOTHING, db_column='cell_line', primary_key=True)
    tf1 = models.CharField(max_length=20)
    tf2 = models.CharField(max_length=20)
    max_distance = models.IntegerField()
    cumulative_count_all = models.IntegerField(blank=True, null=True)
    cumulative_count_tss = models.IntegerField(blank=True, null=True)
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
        db_table = 'cell_line_null'
        unique_together = (('cell_line', 'tf1', 'tf2', 'max_distance'),)


class CellLineTfs(models.Model):
    cell_line = models.CharField(primary_key=True, max_length=20)
    tf = models.CharField(max_length=20)
    use_in_null = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'cell_line_tfs'
        unique_together = (('cell_line', 'tf'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


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
    tf1 = models.CharField(choices=[("", "")], max_length=20)
    tf2 = models.CharField(choices=[("", "")], max_length=20)
    max_dist = models.IntegerField(choices=MAX_DISTANCES, default=1)
    num_min = models.IntegerField()
    num_min_w_tsses = models.DecimalField(max_digits=5, decimal_places=2, blank=True)
    which_tests = models.CharField(max_length=20,choices=TESTS, blank=False, null=False, default=1)
    min_test_num = models.IntegerField()
    pvalue = models.IntegerField(choices=P_VALUES, default=1)



class MyDataEncodeFormModel(models.Model):
    cell = models.CharField(max_length=20)
    method = models.CharField(max_length=20)
    session_id = models.CharField(max_length=100)
    mydata = models.FileField(upload_to="uploaded/")

class AnalysisResults(models.Model):
    tf1 = models.CharField(max_length=20)
    tf2 = models.CharField(max_length=20)
    avg = models.DecimalField(max_digits=20, decimal_places=2, )
    median = models.DecimalField(max_digits=20, decimal_places=2)
    mad = models.DecimalField(max_digits=20, decimal_places=2)
    tail_1000 = models.DecimalField(max_digits=20, decimal_places=2)