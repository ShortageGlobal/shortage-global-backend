from django.db import models
from django.db.models.signals import pre_save, post_save

# Create your models here.

class History:

    def attach_listener(self, sender, attribute):
        pre_save.connect()

        pass

    def add_record(self, record, **kwargs):
        pass

class HistoricEntry(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)

    parent_pk = models.CharField(db_index=True)

    record = models.CharField()
    metadata = models.CharField(blank=True, null=True)
