# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-02 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DjangoMigrations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('applied', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_migrations',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Hepg22',
            fields=[
                ('tf1', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('tf2', models.CharField(max_length=20)),
                ('distance', models.IntegerField()),
                ('count_all', models.IntegerField()),
                ('count_tss', models.IntegerField()),
                ('cumulative_count_all', models.IntegerField()),
            ],
            options={
                'db_table': 'hepg2_2',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Hepg22Null',
            fields=[
                ('tf1', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('tf2', models.CharField(max_length=20)),
                ('max_distance', models.IntegerField()),
                ('average', models.FloatField(blank=True, null=True)),
                ('median', models.FloatField(blank=True, null=True)),
                ('mad', models.FloatField(blank=True, null=True)),
                ('tail_percentage_array', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'hepg2_2_null',
                'managed': False,
            },
        ),
    ]
