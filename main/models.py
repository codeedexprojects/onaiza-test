import uuid
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_id = models.PositiveIntegerField(db_index=True, unique=True)
    creator = models.ForeignKey(
        "auth.User", blank=True, related_name="creator_%(class)s_objects", on_delete=models.CASCADE)
    updater = models.ForeignKey("auth.User", blank=True, null=True,
                                related_name="updater_%(class)s_objects", on_delete=models.CASCADE)
    date_added = models.DateTimeField(db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_reason = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        abstract = True


class Mode(models.Model):
    readonly = models.BooleanField(default=False)
    maintenance = models.BooleanField(default=False)
    down = models.BooleanField(default=False)

    class Meta:
        db_table = 'mode'
        verbose_name = _('mode')
        verbose_name_plural = _('mode')
        ordering = ('id',)

    class Admin:
        list_display = ('id', 'readonly', 'maintenance', 'down')

    def __str__(self):
        return str(self.id)


class Settings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    counter = models.PositiveIntegerField()
    prefix = models.CharField(max_length=128)
    project_prefix = models.CharField(max_length=128)
    product_prefix = models.CharField(max_length=128)
    purchase_prefix = models.CharField(max_length=128)
    sale_prefix = models.CharField(max_length=128)
    payment_prefix = models.CharField(max_length=128)

    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'setting'
        verbose_name = _('setting')
        verbose_name_plural = _('settings')
        ordering = ('prefix',)

    def __unicode__(self):
        return self.prefix


class AppUpdate(models.Model):
    version = models.CharField(max_length=20)
    force_update = models.BooleanField(default=False)
    update_recomented = models.BooleanField(default=False)

    class Meta:
        db_table = 'app_update'
        verbose_name = _('Application Update')
        verbose_name_plural = _('Application Updates')
        ordering = ('id',)

    def __str__(self):
        return f"Version : {self.version}"
