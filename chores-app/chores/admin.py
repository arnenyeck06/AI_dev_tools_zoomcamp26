from django.contrib import admin

from .models import Chore, ChoreAssignment, Grade, Household, Membership


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'household', 'role', 'joined_at')
    list_filter = ('role', 'household')
    search_fields = ('user__username',)


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ('title', 'household', 'chore_type', 'active', 'created_at')
    list_filter = ('chore_type', 'active', 'household')
    search_fields = ('title',)


@admin.register(ChoreAssignment)
class ChoreAssignmentAdmin(admin.ModelAdmin):
    list_display = ('chore', 'assignee', 'due_date', 'week_start', 'status', 'completed_at')
    list_filter = ('status', 'chore__household')
    date_hierarchy = 'due_date'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'score', 'graded_by', 'graded_at')
    list_filter = ('score',)
