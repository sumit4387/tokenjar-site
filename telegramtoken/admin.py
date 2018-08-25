# -*- coding: utf-8 -*-
from django.contrib import admin

from django.db.models import ManyToManyField
from django.forms import CheckboxSelectMultiple
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions, takes_instance_or_queryset


from telegramtoken.models import (
    TelegramToken,
     WalletID,
    ActivationMode,
    TelegramContent,
    TelegramTransaction)


admin.site.site_header = 'Telegram Token'
admin.site.site_title = 'Telegram Token'
admin.site.index_title = ''
admin.site.disable_action('delete_selected')

# admin.site.login_template = 'login.html'

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


from .forms import UserAdminCreationForm, UserAdminChangeForm
from .models import User

class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'admin')
    list_filter = ('admin',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields':()}),
        ('Permissions', {'fields': ('admin',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)



# Remove Group Model from admin. We're not using it.
admin.site.unregister(Group)

class RegisterableMixin(DjangoObjectActions):

    actions = ['action_register']
    change_actions = ['action_register']

    @takes_instance_or_queryset
    def action_register(self, request, queryset):
        for obj in queryset:
            if not obj.txid:
                txid = obj.register()
                obj.txid = txid
                obj.save()
    action_register.label = 'Register on Blockchain'
    action_register.short_description = 'Register on Content Blockchain'

    def admin_txid(self, obj):
        if obj.txid:
            url = 'http://explorer.coblo.net/tx/{}?raw'.format(obj.txid)
            link = '<a href={} target="_blank">{}</a>'.format(url, obj.txid)
            return mark_safe(link)
    admin_txid.short_description = 'Transaction-ID'

    def admin_registered(self, obj):
        return bool(obj.txid)
    admin_registered.boolean = True
    admin_registered.short_description = 'Registered'

@admin.register(WalletID)
class WalletIDAdmin(admin.ModelAdmin):
    list_display = 'address', 'memo', 'owner'
    fields = 'owner', 'address', 'memo'
    readonly_fields = ()
    search_fields = ('user__username', 'address')
    actions = None


@admin.register(TelegramToken)
class TelegramTokenAdmin(RegisterableMixin, admin.ModelAdmin):

    list_display = ('ident', 'info', 'administrator', 'organization', 'material', 'admin_registered')
    fieldsets = (
        ('Basics', {
            'fields': ('ident',  'material', 'info', 'administrator', 'organization'),
        }),
        ('TelegramToken Settings', {
            'fields': ('transaction_model', ),
        }),
        ('Blockchain Info', {
            'fields': ('admin_txid',)
        })
    )

    formfield_overrides = {
        ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    readonly_fields = ('ident', 'admin_txid')


@admin.register(ActivationMode)
class ActivationModeAdmin(admin.ModelAdmin):
    list_display = ('ident', 'description',)
    actions = None

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    # def save_model(self, request, obj, form, change):
    #     pass



@admin.register(TelegramContent)
class TelegramContentAdmin(RegisterableMixin, admin.ModelAdmin):
    list_display = ('title', 'name',  'ident', 'extra', 'admin_registered')
    fields = ('ident', 'title', 'extra', 'file', 'admin_txid')
    readonly_fields = 'ident', 'admin_txid'
    search_fields = ('title', 'name')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return True




@admin.register(TelegramTransaction)
class TokenTransactionAdmin(RegisterableMixin, admin.ModelAdmin):
    list_display = 'telegram_token', 'recipient', 'admin_registered'
    fields = 'telegram_token', 'recipient', 'admin_txid'
    readonly_fields = 'admin_txid',

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Only tokenized telegram token selectable"""
        if db_field.name == "telegram_token":
            kwargs["queryset"] = TelegramToken.objects.tokenized()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return True

