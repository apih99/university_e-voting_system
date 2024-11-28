from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from .models import User, Faculty, Profile
from .forms import CustomUserCreationForm, CustomUserChangeForm

class RoleFilter(SimpleListFilter):
    title = _('role type')
    parameter_name = 'role_type'

    def lookups(self, request, model_admin):
        return [
            ('voter', _('Voter')),
            ('candidate', _('Candidate')),
            ('admin', _('Administrator')),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role=self.value())
        return queryset

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    
    list_display = ('username', 'full_name', 'email', 'student_id', 'faculty', 'role_badge', 
                   'verification_status', 'is_staff', 'last_login_display')
    list_filter = (RoleFilter, 'faculty', 'is_verified', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'student_id', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'student_id', 'phone_number', 'faculty')
        }),
        ('Roles and Permissions', {
            'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser'),
            'classes': ('wide',),
            'description': 'Configure user roles and system permissions'
        }),
        ('Group Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',),
            'description': 'Manage group memberships and specific permissions'
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('User Details', {
            'fields': ('first_name', 'last_name', 'student_id', 'phone_number', 'faculty'),
        }),
        ('Role Assignment', {
            'fields': ('role', 'is_staff', 'is_superuser'),
            'description': 'Assign appropriate role and permissions'
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or "-"
    full_name.admin_order_field = 'first_name'
    
    def role_badge(self, obj):
        colors = {
            'admin': '#dc3545',  # Red for admin
            'voter': '#28a745',  # Green for voter
            'candidate': '#007bff',  # Blue for candidate
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.role, '#6c757d'),
            obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    
    def verification_status(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Verified</span>'
            )
        return format_html(
            '<span style="color: #dc3545;"><i class="fas fa-times-circle"></i> Unverified</span>'
        )
    verification_status.short_description = 'Verification'
    
    def last_login_display(self, obj):
        if obj.last_login:
            return obj.last_login.strftime("%Y-%m-%d %H:%M")
        return "-"
    last_login_display.short_description = 'Last Login'
    
    def save_model(self, request, obj, form, change):
        # If creating a new admin user, automatically set is_staff and is_superuser
        if not change and obj.role == 'admin':
            obj.is_staff = True
            obj.is_superuser = True
            messages.info(request, f'User {obj.username} has been granted admin privileges.')
        
        # If changing role to admin
        elif change and 'role' in form.changed_data and obj.role == 'admin':
            obj.is_staff = True
            obj.is_superuser = True
            messages.info(request, f'User {obj.username} has been granted admin privileges.')
        
        # If removing admin role
        elif change and 'role' in form.changed_data and obj.role != 'admin':
            # Keep superuser status if explicitly set
            if not obj.is_superuser:
                obj.is_staff = False
            messages.warning(request, f'Admin privileges have been revoked for {obj.username}.')
        
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            # Non-superusers can't change these fields for existing users
            return self.readonly_fields + ('is_superuser', 'user_permissions', 'groups')
        return self.readonly_fields

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_winners', 'student_count', 'created_at')
    search_fields = ('name',)
    list_filter = ('max_winners',)
    
    def student_count(self, obj):
        return User.objects.filter(faculty=obj).count()
    student_count.short_description = 'Number of Students'

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_role', 'user_faculty', 'is_general_candidate', 'profile_completion')
    list_filter = ('is_general_candidate', 'user__role', 'user__faculty')
    search_fields = ('user__username', 'user__email', 'bio')
    raw_id_fields = ('user',)
    
    def user_role(self, obj):
        return obj.user.get_role_display()
    user_role.short_description = 'Role'
    
    def user_faculty(self, obj):
        return obj.user.faculty
    user_faculty.short_description = 'Faculty'
    
    def profile_completion(self, obj):
        fields = [obj.bio, obj.photo, obj.personal_statement]
        completed = sum(1 for f in fields if f)
        percentage = (completed / len(fields)) * 100
        
        if percentage >= 75:
            color = '#28a745'
        elif percentage >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'
            
        return format_html(
            '<div style="width: 100px; background-color: #f8f9fa; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px;"></div>'
            '</div> {}%',
            percentage, color, int(percentage)
        )
    profile_completion.short_description = 'Profile Completion'
