from django.contrib import admin
from .models import *

admin.site.register(Topic)
admin.site.register(Tag)
admin.site.register(Publication)
admin.site.register(Collection)
admin.site.register(CollectionPublication)
admin.site.register(Message)
