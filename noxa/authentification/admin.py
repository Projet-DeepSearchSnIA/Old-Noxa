from django.contrib import admin
from .models import *

admin.site.site_header = "Noxa Admin"
admin.site.site_title = "Noxa Admin Portal"
admin.site.index_title = "Welcome to the Noxa Admin Portal"

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'school', 'nb_documents', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')
    ordering = ('username',)
    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Info', {
            'fields': ('photo', 'school', 'bio', 'linkedin', 'github')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_active')
        }),
    )
    add_fieldsets = fieldsets

admin.site.register(User, UserAdmin)

