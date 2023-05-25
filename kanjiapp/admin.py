from django.contrib import admin

# Register your models here.
from kanjiapp.models import Item, ItemId, Tag, TagList, Yomi, Hyoki, Ref, RefList, Eg, EgList

admin.site.register(Item)
admin.site.register(ItemId)
admin.site.register(Tag)
admin.site.register(TagList)
admin.site.register(Yomi)
admin.site.register(Hyoki)
admin.site.register(Ref)
admin.site.register(RefList)
admin.site.register(Eg)
admin.site.register(EgList)