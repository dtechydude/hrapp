from django.contrib import admin
from .models import StaffRank, Staff, StaffAttendance
from import_export.admin import ImportExportModelAdmin



    
class StaffAdmin(ImportExportModelAdmin):
    list_display = ( 'user', 'last_name', 'first_name', 'phone_home', 'qualification' )
    search_fields = ('first_name', 'last_name')
    list_filter = ['staff_rank',]
    ordering = ['dept_assigned__name', 'first_name']
    raw_id_fields = ['user', 'dept_assigned']



# attendance/admin.py

@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):

    list_display = (
        'employee',
        'date',
        'check_in_time',
        'check_out_time',
        'status',
        'is_late',
    )
    raw_id_fields = (
        'employee',
        'checked_in_by',
        'checked_out_by',
    )

    list_filter = (
        'status',
        'is_late',
        'date',
    )

    search_fields = (
        'employee__user__first_name',
        'employee__user__last_name',
        'employee__staff_id',
    )

    ordering = ('-date',)






# admin.site.register(StaffCategory)
admin.site.register(Staff, StaffAdmin)

