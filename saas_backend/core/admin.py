from django.contrib import admin
from .models import UserProfile, Project, Task


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'department']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'status', 'start_date', 'end_date', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['members']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assigned_to', 'priority', 'status', 'due_date']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description', 'project__name']
    readonly_fields = ['created_at', 'updated_at']