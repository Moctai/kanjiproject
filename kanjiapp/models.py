from cgitb import text
from ctypes.wintypes import tagMSG
from time import clock_settime
from django.db import models

# Create your models here.

class Item(models.Model):
    item_id = models.PositiveIntegerField()
    classification = models.CharField(max_length=5, blank=True, null=True)
    txt = models.TextField(blank=True, null=True)
    odr = models.IntegerField(blank=True, null=True)
    list_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'item'


class ItemId(models.Model):

    class Meta:
        managed = False
        db_table = 'item_id'


class Tag(models.Model):
    item_id = models.PositiveIntegerField()
    tag = models.ForeignKey('TagList', models.DO_NOTHING, db_column='tag')

    class Meta:
        managed = False
        db_table = 'tag'


class TagList(models.Model):
    txt = models.CharField(primary_key=True, max_length=255)

    class Meta:
        managed = False
        db_table = 'tag_list'


class Yomi(models.Model):
    item = models.ForeignKey('ItemId', models.DO_NOTHING, related_name='yomi')
    txt = models.TextField(blank=True, null=True)
    odr = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'yomi'


class Hyoki(models.Model):
    item = models.ForeignKey('ItemId', models.DO_NOTHING, related_name='hyoki')
    txt = models.TextField(blank=True, null=True)
    odr = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'hyoki'


class Means(models.Model):
    item = models.ForeignKey('ItemId', models.DO_NOTHING, related_name='means')
    txt = models.TextField(blank=True, null=True)
    odr = models.IntegerField(blank=True, null=True)
    list_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'means'


class Ex(models.Model):
    item = models.ForeignKey('ItemId', models.DO_NOTHING, related_name='ex')
    txt = models.TextField(blank=True, null=True)
    odr = models.IntegerField(blank=True, null=True)
    list_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ex'


class Ref(models.Model):
    item_id = models.PositiveIntegerField(blank=True, null=True)
    ref = models.ForeignKey('RefList', models.DO_NOTHING)
    yomi = models.TextField(db_collation='utf8mb4_bin', blank=True, null=True)
    hyoki = models.TextField(db_collation='utf8mb4_bin')
    note = models.TextField(blank=True, null=True)
    tag = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ref'


class RefList(models.Model):
    author = models.TextField(blank=True, null=True)
    editor = models.TextField(blank=True, null=True)
    translator = models.TextField(blank=True, null=True)
    others1 = models.TextField(blank=True, null=True)
    p_year = models.TextField()
    title = models.TextField()
    contribution = models.TextField(blank=True, null=True)
    volume = models.TextField(blank=True, null=True)
    edition = models.TextField(blank=True, null=True)
    publisher = models.TextField(blank=True, null=True)
    series = models.TextField(blank=True, null=True)
    others = models.TextField(blank=True, null=True)
    isbn = models.TextField(blank=True, null=True)
    category = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = 'ref_list'


class Eg(models.Model):
    item_id = models.PositiveIntegerField()
    txt = models.TextField(blank=True, null=True)
    odr = models.IntegerField(blank=True, null=True)
    list = models.ForeignKey('EgList', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'eg'


class EgList(models.Model):
    author = models.TextField(blank=True, null=True)
    title = models.TextField()

    class Meta:
        managed = False
        db_table = 'eg_list'