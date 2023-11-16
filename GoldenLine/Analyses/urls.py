from django.urls import path
from . import views

urlpatterns = [
    path('analyses', views.analyses, name='analyses'),
    path('', views.accueil, name='accueil'),
    path('export', views.exporter_donnees, name='export'),
    path('connection', views.connection, name='connection'),
    path('enregistrement', views.enregistrement, name='enregistrement'),
    path('deconnection', views.deconnection, name='deconnection'),
    path('liste_utilisateurs', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('modifier_utilisateur/<str:nom_utilisateur>', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('supprimer_utilisateur/<str:nom_utilisateur>', views.supprimer_utilisateur, name='supprimer_utilisateur')
]