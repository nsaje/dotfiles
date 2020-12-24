from django.db import models


class CreditNotifications(models.Model):
    class Meta:
        app_label = "dash"

    credit = models.OneToOneField("CreditLineItem", related_name="notifications", on_delete=models.CASCADE)
    sent_80_percent = models.BooleanField(null=False, blank=False, default=False)
    sent_90_percent = models.BooleanField(null=False, blank=False, default=False)

    def set_sent_80_percent(self):
        self.sent_80_percent = True
        self.save()

    def set_all(self):
        self.sent_80_percent = True
        self.sent_90_percent = True
        self.save()

    def unset_sent_90_percent(self):
        self.sent_90_percent = False
        self.save()

    def unset_all(self):
        self.sent_80_percent = False
        self.sent_90_percent = False
        self.save()
