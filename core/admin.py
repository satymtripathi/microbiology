from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import PortalUser, Request, Report, RequestHistory

# ------------------------------------------
# 1. Register Custom User Model
# ------------------------------------------
@admin.register(PortalUser)
class PortalUserAdmin(UserAdmin):
    model = PortalUser
    list_display = ('username', 'full_name', 'email', 'role', 'pin_code', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role', 'full_name', 'pin_code', 'reading_centre_code')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role', 'full_name', 'pin_code', 'reading_centre_code')}),
    )


# ------------------------------------------
# 2. Register Request Model
# ------------------------------------------
@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'doctor', 'centre_name', 'patient_id', 'on_meds', 'status')
    list_filter = ('status', 'centre_name', 'on_meds', 'meds_category')
    search_fields = ('patient_id', 'doctor__full_name')


# ------------------------------------------
# 3. Register Report Model
# ------------------------------------------
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('request', 'rc_code', 'lab_id', 'quality', 'sample_suitability', 'auth_by')
    list_filter = ('quality', 'sample_suitability')
    search_fields = ('request__patient_id', 'rc_code', 'lab_id')


# ------------------------------------------
# 4. Register RequestHistory Model
# ------------------------------------------
@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ('request', 'action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('request__patient_id', 'user__full_name')
    readonly_fields = ('timestamp',)
