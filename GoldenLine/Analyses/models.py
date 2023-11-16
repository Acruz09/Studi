from django.db import models


# Modèle pour représenter un client
class Client(models.Model):
    identifiant_client = models.AutoField(primary_key=True)
    nombre_enfants = models.IntegerField()
    categorie_socioprofessionnelle = models.CharField(max_length=50)
    prix_panier = models.DecimalField(max_digits=10, decimal_places=2)
    identifiant_collecte = models.ForeignKey('Collecte', on_delete=models.CASCADE)

    def __str__(self):
        return f"Client {self.identifiant_client}"

    class Meta:
        db_table = 'client'


# Modèle pour représenter une collecte
class Collecte(models.Model):
    identifiant_collecte = models.AutoField(primary_key=True)
    detail_panier = models.JSONField()

    def __str__(self):
        return f"Collecte {self.identifiant_collecte}"

    class Meta:
        db_table = 'collecte'
