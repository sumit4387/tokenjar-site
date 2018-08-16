from django.db import models


class Coins(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    base = models.CharField(max_length=255, blank=True, null=True)
    symbol = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    volumeDay = models.CharField(max_length=255, blank=True, null=True)
    telegram = models.CharField(max_length=255, blank=True, null=True)
    highDay = models.CharField(max_length=255, blank=True, null=True)
    priceChangeRateDay = models.CharField(max_length=255, blank=True, null=True)
    type = models.IntegerField(null=True, default=0)
    priceChangeDay = models.CharField(max_length=255, blank=True, null=True)
    lowDay = models.CharField(max_length=255, blank=True, null=True)
    price = models.CharField(max_length=255, blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    pair = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(null=True)
    decimals = models.CharField(max_length=50, blank=True, null=True)


    def __str__(self):
        return str(self.name)

    class Meta:
        db_table = "coins"
