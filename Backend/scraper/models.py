from django.db import models

class TunepsOffer(models.Model):
    num_consultation = models.CharField(max_length=255, unique=True)
    client = models.CharField(max_length=255)
    date_publication = models.DateField()
    intitulé_projet = models.TextField()
    date_expiration = models.DateField()
    epBidMasterId = models.CharField(max_length=255)
    lien = models.URLField()

    def __str__(self):
        return self.num_consultation
