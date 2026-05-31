from django.contrib import admin
from .models import Booking, JobCategory, WorkerProfile, WorkerWorkImage


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    search_fields = ('name',)


class WorkerWorkImageInline(admin.TabularInline):
    model = WorkerWorkImage
    extra = 0


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'price', 'is_online', 'experience_years')
    list_filter = ('category', 'is_online')
    search_fields = ('user__username', 'user__email', 'category')
    inlines = [WorkerWorkImageInline]


@admin.register(WorkerWorkImage)
class WorkerWorkImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'worker', 'caption', 'sort_order', 'created_at')
    list_filter = ('created_at',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'worker', 'service_category', 'status', 'scheduled_at')
    list_filter = ('status', 'service_category')
