import csv
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, Permission, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from .models import *


@login_required
@permission_required("Analyses.view_client", raise_exception=True)
def analyses(request):
    template = 'analyses.html'

    moyennes = Client.objects.values('categorie_socioprofessionnelle').annotate(moyenne_prix=models.Avg('prix_panier'))

    #### Récupérer toutes les catégories

    # Récupérer toutes les collectes
    collectes = Collecte.objects.all()

    # Créer un ensemble pour stocker les catégories uniques
    categories = []

    # Parcourir toutes les collectes et extraire les catégories
    for collecte in collectes:
        detail_panier = collecte.detail_panier
        for categorie in detail_panier:
            if categorie not in categories:
                categories.append(categorie)

    #### ####

    #### Récupérer toutes les catégories socio-professionnelle
    clients = Client.objects.all()

    # Créer un ensemble pour stocker les catégories uniques
    categorie_socioprofessionnelle = []

    # Parcourir toutes les collectes et extraire les catégories
    for client in clients:
        categorie_socio = client.categorie_socioprofessionnelle
        if categorie_socio not in categorie_socioprofessionnelle:
            categorie_socioprofessionnelle.append(categorie_socio)

    #### ####

    valeurs = {}
    for categorie in categories:
        valeurs[categorie] = [0] * len(categorie_socioprofessionnelle)

    for client in clients:
        detail_panier = client.identifiant_collecte.detail_panier
        categorie_socio = client.categorie_socioprofessionnelle
        for categorie, valeur in detail_panier.items():
            index = categorie_socioprofessionnelle.index(categorie_socio)
            valeurs[categorie][index] += valeur

    for liste in valeurs.values():
        for i in range(len(liste)):
            liste[i] = round(liste[i], 2)

    context = {
        'moyennes': moyennes,
        'categories': categories,
        'categorie_socioprofessionnelle': categorie_socioprofessionnelle,
        'valeurs': valeurs

    }

    return render(request, template, context)


@login_required
@permission_required("Analyses.view_collecte", raise_exception=True)
def exporter_donnees(request):
    if request.method == 'POST':
        # Récupérer le nombre de lignes à exporter depuis le formulaire
        nombre_lignes = int(request.POST.get('nombre_lignes', 10))  # La valeur par défaut est 10 si non spécifiée

        # Récupérer les données à exporter depuis la base de données
        donnees = Collecte.objects.all()[:nombre_lignes]  # Récupérez les premières 'nombre_lignes' lignes

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="export.csv"'

        writer = csv.writer(response)
        writer.writerow(['identifiant_collecte', 'detail_panier'])  # Entêtes (remplacez par les noms des champs de votre modèle)

        for donnee in donnees:
            writer.writerow([donnee.identifiant_collecte, donnee.detail_panier])  # Remplacez les noms de champ

        return response

    # Générez un formulaire pour que l'utilisateur spécifie le nombre de lignes
    return render(request, 'exportation_donnees.html')


def accueil(request):
    return render(request, 'accueil.html')


@login_required
@permission_required("auth.add_user", raise_exception=True)
def enregistrement(request):
    if request.method == "POST":
        nom_utilisateur = request.POST['utilisateur']
        nom = request.POST['nom']
        prenom = request.POST['prenom']
        email = request.POST['email']
        mdp = request.POST['mdp']
        mdp2 = request.POST['mdp2']

        view_client = request.POST.get('view_client') == 'on'
        view_collecte = request.POST.get('view_collecte') == 'on'
        admin = request.POST.get('admin') == 'on'

        if User.objects.filter(username=nom_utilisateur):
            messages.error(request, "Ce nom a été déjà pris")
            return redirect("/enregistrement")
        if User.objects.filter(email=email):
            messages.error(request, "Cette email possède déjà un compte")
            return redirect("/enregistrement")
        if not nom_utilisateur.isalnum():
            messages.error(request, "Le nom doit utilisé uniquement des caractères alphanumériques")
            return redirect("/enregistrement")
        if mdp != mdp2:
            messages.error(request, "Les deux mots de passes ne sont pas identiques")
            return redirect("/enregistrement")
        utilisateur = User.objects.create_user(nom_utilisateur, email, mdp)
        utilisateur.first_name = nom
        utilisateur.last_name = prenom

        if admin:
            groupe, created = Group.objects.get_or_create(name="administrateurs")
            utilisateur.groups.add(groupe)
        else:
            if view_client:
                permission_view_client = Permission.objects.get(codename='view_client')
                utilisateur.user_permissions.add(permission_view_client)

            if view_collecte:
                permission_view_collecte = Permission.objects.get(codename='view_collecte')
                utilisateur.user_permissions.add(permission_view_collecte)

        utilisateur.save()
        messages.success(request, 'Votre compte a été créer avec succès')
        return redirect('/')
    return render(request, 'enregistrement.html')


@login_required
@permission_required("auth.view_user", raise_exception=True)
def liste_utilisateurs(request):
    utilisateurs = User.objects.all()
    return render(request, 'liste_utilisateurs.html', {'utilisateurs': utilisateurs})


@login_required
@permission_required("auth.change_user", raise_exception=True)
def modifier_utilisateur(request, nom_utilisateur):
    utilisateur = get_object_or_404(User, username=nom_utilisateur)

    if request.method == 'POST':

        # Vérifier si le nom d'utilisateur existe déjà
        nouveau_username = request.POST.get('utilisateur')
        if nouveau_username != nom_utilisateur and User.objects.filter(username=nouveau_username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")
            return redirect(reverse('modifier_utilisateur', args=[nom_utilisateur]))
        # Vérifier si l'adresse email existe déjà
        nouvel_email = request.POST.get('email')
        if nouvel_email != utilisateur.email and User.objects.filter(email=nouvel_email).exists():
            messages.error(request, "Cet email est déjà associé à un compte. Veuillez en choisir un autre.")
            return redirect(reverse('modifier_utilisateur', args=[nom_utilisateur]))

        # Vérifier si le nom d'utilisateur est alphanumérique
        if not nouveau_username.isalnum():
            messages.error(request, "Le nom d'utilisateur doit utiliser uniquement des caractères alphanumériques.")
            return redirect(reverse('modifier_utilisateur', args=[nom_utilisateur]))

        # Mettre à jour les données de l'utilisateur
        utilisateur.username = request.POST.get('utilisateur')
        utilisateur.first_name = request.POST.get('nom')
        utilisateur.last_name = request.POST.get('prenom')
        utilisateur.email = request.POST.get('email')

        # Mettre à jour les groupes de l'utilisateur
        utilisateur.groups.clear()
        admin = request.POST.get('admin') == 'on'
        if admin:
            groupe, created = Group.objects.get_or_create(name="administrateurs")
            utilisateur.groups.add(groupe)

        # Mettre à jour les permissions de l'utilisateur
        utilisateur.user_permissions.clear()

        view_client = request.POST.get('view_client') == 'on'
        view_collecte = request.POST.get('view_collecte') == 'on'
        if view_client:
            permission_view_client = Permission.objects.get(codename='view_client')
            utilisateur.user_permissions.add(permission_view_client)

        if view_collecte:
            permission_view_collecte = Permission.objects.get(codename='view_collecte')
            utilisateur.user_permissions.add(permission_view_collecte)

        # Mettre à jour le mot de passe si fourni
        password = request.POST.get('mdp')
        if password:
            utilisateur.set_password(password)

        utilisateur.save()

        # utilisateurs = User.objects.all()
        return redirect('liste_utilisateurs')

    admin = utilisateur.groups.filter(name='administrateurs').exists()
    permission_view_client = utilisateur.has_perm('Analyses.view_client')
    permission_view_collecte = utilisateur.has_perm('Analyses.view_collecte')

    context = {
        'utilisateur': utilisateur,
        'admin': admin,
        'permission_view_client': permission_view_client,
        'permission_view_collecte': permission_view_collecte
    }

    return render(request, 'modifier_utilisateur.html', context)


@login_required
@permission_required("auth.delete_user", raise_exception=True)
def supprimer_utilisateur(request, nom_utilisateur):
    # Récupérer l'utilisateur à supprimer
    utilisateur = get_object_or_404(User, username=nom_utilisateur)

    # Supprimer l'utilisateur
    utilisateur.delete()

    # Ajouter un message pour informer de la suppression
    messages.success(request, f"L'utilisateur {nom_utilisateur} a été supprimé avec succès.")

    # Rediriger vers la liste des utilisateurs
    return redirect('liste_utilisateurs')


def connection(request):
    if request.method == "POST":
        nom_utilisateur = request.POST['utilisateur']
        mdp = request.POST['mdp']
        utilisateur = authenticate(username=nom_utilisateur, password=mdp)
        if utilisateur is not None:
            login(request, utilisateur)
            nom_utilisateur = utilisateur.first_name
            return render(request, 'accueil.html', {'nom_utilisateur': nom_utilisateur})
        else:
            messages.error(request, 'Mauvaise authentification')
            return redirect('connection')
    return render(request, 'connection.html')


def deconnection(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecter')
    return redirect('/')