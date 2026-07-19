from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import SupportTicket, User

admin.site.register(User, UserAdmin)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subject', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    list_editable = ('status',)
    search_fields = ('subject', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
