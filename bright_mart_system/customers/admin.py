from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Customer

# Define an inline interface for the Customer model
class CustomerInline(admin.StackedInline):
    model = Customer
    can_delete = False
    verbose_name_plural = 'Customer Profile Data'

# Extend the default User Admin configuration to include your Customer fields
class UserAdmin(BaseUserAdmin):
    inlines = (CustomerInline, )

# Re-register the User mapping
admin.site.unregister(User)
admin.site.register(User, UserAdmin)