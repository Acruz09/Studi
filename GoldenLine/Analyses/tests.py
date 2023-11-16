import csv
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.messages import get_messages
from django.urls import reverse
from .models import Client, Collecte


class TestBDD(TestCase):
    def setUp(self):
        # Créez des données pour les tests
        self.collecte = Collecte.objects.create(detail_panier={'produit1': 30.5, 'produit2': 20.25})
        self.client = Client.objects.create(
            nombre_enfants=2,
            categorie_socioprofessionnelle='Professionnel',
            prix_panier=50.75,
            identifiant_collecte=self.collecte
        )

    def test_str_client(self):
        # Vérifiez que la méthode __str__ renvoie la représentation attendue
        self.assertEqual(str(self.client), f"Client {self.client.identifiant_client}")

    def test_str_collect(self):
        # Vérifiez que la méthode __str__ renvoie la représentation attendue
        self.assertEqual(str(self.collecte), f"Collecte {self.collecte.identifiant_collecte}")

    def test_meta_db_table(self):
        # Vérifiez que la table de la base de données est correctement définie
        self.assertEqual(Client._meta.db_table, 'client')

    def test_meta_db_table(self):
        # Vérifiez que la table de la base de données est correctement définie
        self.assertEqual(Collecte._meta.db_table, 'collecte')

    def test_champ_nombre_enfants(self):
        # Vérifiez que le champ nombre_enfants est correctement défini
        field = Client._meta.get_field('nombre_enfants')
        self.assertEqual(field.get_internal_type(), 'IntegerField')

    def test_champ_categorie_socioprofessionnelle(self):
        # Vérifiez que le champ categorie_socioprofessionnelle est correctement défini
        field = Client._meta.get_field('categorie_socioprofessionnelle')
        self.assertEqual(field.get_internal_type(), 'CharField')
        self.assertEqual(field.max_length, 50)

    def test_champ_prix_panier(self):
        # Vérifiez que le champ prix_panier est correctement défini
        field = Client._meta.get_field('prix_panier')
        self.assertEqual(field.get_internal_type(), 'DecimalField')
        self.assertEqual(field.max_digits, 10)
        self.assertEqual(field.decimal_places, 2)


class TestAnalysesView(TestCase):
    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(username='user', password='password')

        # Créer des données dans la base de donnée pour le test
        collecte = Collecte.objects.create(identifiant_collecte=1, detail_panier={'categorie1': 10, 'categorie2': 20})
        Client.objects.create(identifiant_client=1, nombre_enfants=5, categorie_socioprofessionnelle='categorie', prix_panier=30, identifiant_collecte=collecte)

    def test_analyses_view_avec_permission(self):
        # Ajouter les permissions à l'utilisateur
        permission = Permission.objects.get(codename='view_client')
        self.user.user_permissions.add(permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Accéder à la vue
        response = self.client.get(reverse('analyses'))

        # Vérifier que la vue renvoie le code 200
        self.assertEqual(response.status_code, 200)

        # Vérifier que les données nécessaires sont présentes dans le contexte
        self.assertIn('moyennes', response.context)
        self.assertIn('categories', response.context)
        self.assertIn('categorie_socioprofessionnelle', response.context)
        self.assertIn('valeurs', response.context)

    def test_analyses_view_sans_permission(self):
        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Accéder à la vue
        response = self.client.get(reverse('analyses'))

        # Vérifier que la vue renvoie le code 403
        self.assertEqual(response.status_code, 403)

    def test_analyses_view_redirection_non_conncter(self):
        # Accéder à la vue sans s'identifier
        response = self.client.get(reverse('analyses'))

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)


class TestExportationDonneesView(TestCase):
    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(username='user', password='password')

        # Créer des données dans la base de doneées pour le test
        collecte = Collecte.objects.create(identifiant_collecte=1, detail_panier={'categorie1': 10, 'categorie2': 20})
        Collecte.objects.create(identifiant_collecte=2, detail_panier={'categorie1': 20, 'categorie2': 200})
        Collecte.objects.create(identifiant_collecte=3, detail_panier={'categorie1': 40, 'categorie2': 25})
        Client.objects.create(identifiant_client=1, nombre_enfants=5, categorie_socioprofessionnelle='categorie', prix_panier=30, identifiant_collecte=collecte)

    def test_exporter_donnees_avec_permission(self):
        # Donner les permissions à l'utilisateur
        permission = Permission.objects.get(codename='view_collecte')
        self.user.user_permissions.add(permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')
        # Accéder à la vue
        response = self.client.get(reverse('export'))

        # Vérifier que la vue renvoie le code 200
        self.assertEqual(response.status_code, 200)

        # Récupérer l'URL de la vue exporter_donnees
        url = reverse('export')

        # Envoyez une requête POST à l'URL
        response = self.client.post(url, {'nombre_lignes': 2})

        # Vérifiez que la réponse a un code 200
        self.assertEqual(response.status_code, 200)

        # Vérifiez que le type de contenu est 'text/csv'
        self.assertEqual(response['Content-Type'], 'text/csv')

        # Vérifier le contenu du fichier CSV
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(content.splitlines())
        rows = list(csv_reader)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0], ['identifiant_collecte', 'detail_panier'])
        self.assertEqual(rows[1], ['1', "{'categorie1': 10, 'categorie2': 20}"])
        self.assertEqual(rows[2], ['2', "{'categorie1': 20, 'categorie2': 200}"])

    def test_exporter_donnees_sans_permission(self):
        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Accéder à la vue
        response = self.client.get(reverse('export'))

        # Vérifier que la vue renvoie le code 403
        self.assertEqual(response.status_code, 403)

    def test_exporter_donnees_sans_connection(self):
        # Accéder à la vue
        response = self.client.get(reverse('export'))

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)


class TestEnregistrementView(TestCase):
    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(username='user', password='password')

        # Créer des permissions nécessaires
        self.permission = Permission.objects.get(codename='add_user')

    def test_enregistrement_view_avec_permission(self):
        # Ajouter la permission a l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Accéder à la vue en utilisant une requête GET
        response = self.client.get(reverse('enregistrement'))

        # Vérifier que la vue renvoie le code 200
        self.assertEqual(response.status_code, 200)

    def test_enregistrement_view_sans_permission(self):
        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Accéder à la vue en utilisant une requête GET
        response = self.client.get(reverse('enregistrement'))

        # Vérifier que la vue renvoie le code 403
        self.assertEqual(response.status_code, 403)

    def test_enregistrement_avec_succes_1(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Simuler une requête POST avec des données valides
        response = self.client.post(reverse('enregistrement'), {
            'utilisateur': 'newuser',
            'nom': 'Test',
            'prenom': 'User',
            'email': 'test@example.com',
            'mdp': 'password2',
            'mdp2': 'password2',
            'admin': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page d'acceuil
        self.assertRedirects(response, reverse('accueil'))

        # Vérifier que l'utilisateur a été créé
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Vérifier que l'utilisateur a été ajouté au groupe administrateurs
        utilisateur = User.objects.get(username='newuser')
        self.assertTrue(utilisateur.groups.filter(name='administrateurs').exists())

    def test_enregistrement_avec_succes_2(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Simuler une requête POST avec des données valides
        response = self.client.post(reverse('enregistrement'), {
            'utilisateur': 'newuser',
            'nom': 'Test',
            'prenom': 'User',
            'email': 'test@example.com',
            'mdp': 'password2',
            'mdp2': 'password2',
            'view_client': 'on',
            'view_collecte': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page d'accueil
        self.assertRedirects(response, reverse('accueil'))

        # Vérifier que le nouvel utilisateur a été créé
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Vérifier que le nouvel utilisateur possède les différentes authorisations
        utilisateur = User.objects.get(username='newuser')
        self.assertTrue(utilisateur.has_perm('Analyses.view_client'))
        self.assertTrue(utilisateur.has_perm('Analyses.view_collecte'))

    def test_enregistrement_sans_succes_1(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Simuler une requête POST avec des données invalides (nom d'utilisateur déjà existant)
        User.objects.create_user(username='newuser', password='password2')

        response = self.client.post(reverse('enregistrement'), {
            'utilisateur': 'newuser',
            'nom': 'Test',
            'prenom': 'User',
            'email': 'test@example.com',
            'mdp': 'password3',
            'mdp2': 'password3',
            'admin': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page d'enregistrement
        self.assertRedirects(response, reverse('enregistrement'))

        # Vérifier le message d'erreur
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Ce nom a été déjà pris")

    def test_enregistrement_sans_succes_2(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Simuler une requête POST avec des données invalides (email déjà existant)
        User.objects.create_user(username='user2', password='password2', email='test@example.com')
        response = self.client.post(reverse('enregistrement'), {
            'utilisateur': 'newuser',
            'nom': 'Test',
            'prenom': 'User',
            'email': 'test@example.com',
            'mdp': 'password3',
            'mdp2': 'password3',
            'admin': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page d'enregistrement
        self.assertRedirects(response, reverse('enregistrement'))

        # Vérifier le message d'erreur
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Cette email possède déjà un compte")

    def test_enregistrement_sans_succes_3(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Simuler une requête POST avec des données invalides (nom d'utilisateur pas alphnumerique)
        response = self.client.post(reverse('enregistrement'), {
            'utilisateur': 'newuser_2',
            'nom': 'Test',
            'prenom': 'User',
            'email': 'test@example.com',
            'mdp': 'password2',
            'mdp2': 'password2',
            'admin': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page d'enregistrement
        self.assertRedirects(response, reverse('enregistrement'))

        # Vérifier que le nouvel utilisateur n'a pas été créé
        self.assertFalse(User.objects.filter(username='newuser_2').exists())

        # Vérifier le message d'erreur
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Le nom doit utilisé uniquement des caractères alphanumériques")

    def test_enregistrement_view_post_failure_4(self):
        # Ajouter la permission a l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Simuler une requête POST avec des données invalides (nom d'utilisateur pas alphnumerique)
        response = self.client.post(reverse('enregistrement'), {
            'utilisateur': 'newuser',
            'nom': 'Test',
            'prenom': 'User',
            'email': 'test@example.com',
            'mdp': 'password2',
            'mdp2': 'password24',
            'admin': 'on',
        })

        # Vérifier que la vue renvoie le code 302 (redirection)
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page d'enregistrement
        self.assertRedirects(response, reverse('enregistrement'))

        # Vérifier que l'utilisateur n'a pas été créé
        self.assertFalse(User.objects.filter(username='newuser').exists())

        # Vérifier le message d'erreur
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Les deux mots de passes ne sont pas identiques")


class TestModifierUtilisateurView(TestCase):
    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(username='user', password='password')

        # Créer des permissions nécessaires
        self.permission = Permission.objects.get(codename='change_user')

    def test_modifier_utilisateur_view_get_avec_permission(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Créer un utilisateur pour le test
        utilisateur = User.objects.create_user(username='user2', password='password2')

        # Accéder à la vue en utilisant un utilisateur existant
        response = self.client.get(reverse('modifier_utilisateur', args=['user2']))

        # Vérifier que la vue renvoie le code 200
        self.assertEqual(response.status_code, 200)

        # Vérifier que les données de l'utilisateur choisi sont présentes dans le contexte
        self.assertIn('utilisateur', response.context)
        self.assertEqual(response.context['utilisateur'], utilisateur)

    def test_modifier_utilisateur_view_sans_permission(self):
        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Créer un utilisateur pour le test
        User.objects.create_user(username='user2', password='password2')

        # Accéder à la vue en utilisant un utilisateur existant
        response = self.client.get(reverse('modifier_utilisateur', args=['user2']))

        # Vérifier que la vue renvoie le code 403
        self.assertEqual(response.status_code, 403)

    def test_modifier_utilisateur_avec_succes_1(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Créer un utilisateur pour le test
        utilisateur = User.objects.create_user(username='user2', password='password2')

        # Simuler une requête POST avec des données valides
        response = self.client.post(reverse('modifier_utilisateur', args=['user2']), {
            'utilisateur': 'modifieruser2',
            'nom': 'Modifier',
            'prenom': 'User2',
            'email': 'modifier@example.com',
            'mdp': 'password2',
            'admin': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que les données de user2 ont été mises à jour
        utilisateur.refresh_from_db()
        self.assertEqual(utilisateur.username, 'modifieruser2')
        self.assertEqual(utilisateur.first_name, 'Modifier')
        self.assertEqual(utilisateur.last_name, 'User2')
        self.assertEqual(utilisateur.email, 'modifier@example.com')

        # Vérifier que user2 a été ajouté au groupe administrateurs
        self.assertTrue(utilisateur.groups.filter(name='administrateurs').exists())

    def test_modifier_utilisateur_avec_succes_2(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Créer un utilisateur pour le test
        utilisateur = User.objects.create_user(username='user2', password='password2')

        # Simuler une requête POST avec des données valides
        response = self.client.post(reverse('modifier_utilisateur', args=['user2']), {
            'utilisateur': 'modifierduser',
            'nom': 'Modifier',
            'prenom': 'User',
            'email': 'modifier@example.com',
            'mdp': 'password2',
            'view_client': 'on',
            'view_collecte': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que les données de l'utilisateur ont été mises à jour
        utilisateur.refresh_from_db()
        self.assertEqual(utilisateur.username, 'modifierduser')
        self.assertEqual(utilisateur.first_name, 'Modifier')
        self.assertEqual(utilisateur.last_name, 'User')
        self.assertEqual(utilisateur.email, 'modifier@example.com')

        # Vérifier que l'utilisateur possède les autorisations
        self.assertTrue(utilisateur.has_perm('Analyses.view_client'))
        self.assertTrue(utilisateur.has_perm('Analyses.view_collecte'))

    def test_modifier_utilisateur_sans_succes_1(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Créer 2 utilisateurs pour le test
        utilisateur = User.objects.create_user(username='user2', password='password')
        User.objects.create_user(username='user3', password='password2')

        # Simuler une requête POST avec des données invalides
        response = self.client.post(reverse('modifier_utilisateur', args=['user2']), {
            'utilisateur': 'user3',  # Nom d'utilisateur déjà pris
            'nom': 'Modifier',
            'prenom': 'User',
            'email': 'modifier@example.com',
            'mdp': 'password',
            'admin': 'on',
            'view_client': 'on',
            'view_collecte': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page de modification de user2
        self.assertRedirects(response, reverse('modifier_utilisateur', args=['user2']))

        # Vérifier que les données de user2 n'ont pas été modifiées
        utilisateur.refresh_from_db()
        self.assertEqual(utilisateur.username, 'user2')
        self.assertEqual(utilisateur.first_name, '')
        self.assertEqual(utilisateur.last_name, '')
        self.assertEqual(utilisateur.email, '')

        # Vérifier que le message d'erreur est présent dans les messages de la session
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.", messages)

    def test_modifier_utilisateur_sans_succes_2(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Créer 2 utilisateurs pour le test
        utilisateur = User.objects.create_user(username='user2', password='password')
        User.objects.create_user(username='user3', password='password2', email='modifier@example.com')

        # Simuler une requête POST avec des données invalides
        response = self.client.post(reverse('modifier_utilisateur', args=['user2']), {
            'utilisateur': 'user2',
            'nom': 'Modifier',
            'prenom': 'User',
            'email': 'modifier@example.com',
            'mdp': 'password',
            'admin': 'on',
            'view_client': 'on',
            'view_collecte': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page de modification de user2
        self.assertRedirects(response, reverse('modifier_utilisateur', args=['user2']))

        # Vérifier que les données de user2 n'ont pas été modifiées
        utilisateur.refresh_from_db()
        self.assertEqual(utilisateur.username, 'user2')
        self.assertEqual(utilisateur.first_name, '')
        self.assertEqual(utilisateur.last_name, '')
        self.assertEqual(utilisateur.email, '')

        # Vérifier que le message d'erreur est présent dans les messages de la session
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Cet email est déjà associé à un compte. Veuillez en choisir un autre.", messages)

    def test_modifier_utilisateur_sans_succes_3(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter avec l'utilisateur
        self.client.login(username='user', password='password')

        # Créer 2 utilisateurs pour le test
        utilisateur = User.objects.create_user(username='user2', password='password')
        User.objects.create_user(username='user3', password='password2')

        # Simuler une requête POST avec des données invalides
        response = self.client.post(reverse('modifier_utilisateur', args=['user2']), {
            'utilisateur': 'user_2',
            'nom': 'Modifier',
            'prenom': 'User',
            'email': 'modifier@example.com',
            'mdp': 'password',
            'admin': 'on',
            'view_client': 'on',
            'view_collecte': 'on',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page de modification de user2
        self.assertRedirects(response, reverse('modifier_utilisateur', args=['user2']))

        # Vérifier que les données de l'utilisateur n'ont pas été modifiées
        utilisateur.refresh_from_db()
        self.assertEqual(utilisateur.username, 'user2')
        self.assertEqual(utilisateur.first_name, '')
        self.assertEqual(utilisateur.last_name, '')
        self.assertEqual(utilisateur.email, '')

        # Vérifier que le message d'erreur est présent dans les messages de la session
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("Le nom d'utilisateur doit utiliser uniquement des caractères alphanumériques.", messages)


class TestListeUtilisateursView(TestCase):
    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(username='user', password='password')

        # Créer des utilisateurs factices
        User.objects.create_user(username='user2', password='password2')
        User.objects.create_user(username='user3', password='password3')

        # Créer des permissions nécessaires
        self.permission = Permission.objects.get(codename='view_user')

    def test_liste_utilisateurs_view_avec_permission(self):
        # Ajouter la permission à l'utilisateur
        self.user.user_permissions.add(self.permission)

        # Se connecter en tant qu'utilisateur ayant les authorisations
        login_successful = self.client.login(username='user', password='password')
        self.assertTrue(login_successful)

        # Accéder à la vue
        response = self.client.get(reverse('liste_utilisateurs'))

        # Vérifier que la vue renvoie le code 200
        self.assertEqual(response.status_code, 200)

        # Vérifier que les utilisateurs sont présents dans le contexte
        self.assertIn('utilisateurs', response.context)

        # Vérifier que la liste des utilisateurs est la même que celle dans la base de données
        utilisateurs_db = User.objects.all()
        self.assertEqual(list(response.context['utilisateurs']), list(utilisateurs_db))

    def test_liste_utilisateurs_view_sans_permission(self):
        # Se connecter en tant qu'utilisateur
        login_successful = self.client.login(username='user', password='password')
        self.assertTrue(login_successful)

        # Accéder à la vue
        response = self.client.get(reverse('liste_utilisateurs'))

        # Vérifier que la vue renvoie le code 403
        self.assertEqual(response.status_code, 403)


class TestSupprimerUtilisateurView(TestCase):
    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(username='user', password='password')

        # Créer un utilisateur à supprimer
        self.user2 = User.objects.create_user(username='user2', password='password')

        # Créer des permissions nécessaires
        self.permission = Permission.objects.get(codename='delete_user')

    def test_supprimer_utilisateur_view_avec_succes(self):
        # Ajouter à l'utilisateur les authorisations
        self.user.user_permissions.add(self.permission)

        # Se connecter en tant qu'utilisateur ayant les authorisations
        login_successful = self.client.login(username='user', password='password')
        self.assertTrue(login_successful)

        # Accéder à la vue de suppression d'utilisateur
        response = self.client.get(reverse('supprimer_utilisateur', args=['user2']))

        # Vérifier que l'utilisateur a été supprimé
        self.assertFalse(User.objects.filter(username='user2').exists())

        # Vérifier le message de succes
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f"L'utilisateur {self.user2.username} a été supprimé avec succès.")

    def test_supprimer_utilisateur_view_sans_permission(self):
        # Se connecter en tant qu'utilisateur
        login_successful = self.client.login(username='user', password='password')
        self.assertTrue(login_successful)

        # Accéder à la vue de suppression d'utilisateur
        response = self.client.get(reverse('supprimer_utilisateur', args=['user2']))

        # Vérifier que la vue renvoie le code 403
        self.assertEqual(response.status_code, 403)

        # Vérifier que l'utilisateur à supprimer existe toujours
        self.assertTrue(User.objects.filter(username='user2').exists())


class TestConnectionView(TestCase):
    def setUp(self):
        # Créer un utilisateur de test
        self.user = User.objects.create_user(username='user', password='password')

    def test_connection_view_get(self):
        # Accéder à la vue connection
        response = self.client.get(reverse('connection'))

        # Vérifier que la vue renvoie le code 200
        self.assertEqual(response.status_code, 200)

    def test_connection_avec_succes(self):
        # Simuler une requête POST avec des données valides
        response = self.client.post(reverse('connection'), {
            'utilisateur': 'user',
            'mdp': 'password',
        })

        # Vérifier que la vue renvoie le code 200
        self.assertEqual(response.status_code, 200)

        # Vérifier que l'utilisateur est authentifié
        self.assertTrue(response.context['user'].is_authenticated)

    def test_connection_sans_succes(self):
        # Simuler une requête POST avec des données invalides
        response = self.client.post(reverse('connection'), {
            'utilisateur': 'user',
            'mdp': 'password24',
        })

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page de connexion
        self.assertRedirects(response, reverse('connection'))

        # Vérifier que le message d'erreur est présent dans les messages de la session
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('Mauvaise authentification', messages)


class TestDeconnectionView(TestCase):
    def setUp(self):
        # Créer un utilisateur de test
        self.user = User.objects.create_user(username='user', password='password')

    def test_deconnection_view(self):
        # Se connecter avec l'utilisateur
        login_successful = self.client.login(username='user', password='password')
        self.assertTrue(login_successful)

        # Accéder à la vue de déconnexion
        response = self.client.get(reverse('deconnection'))

        # Vérifier que la vue renvoie le code 302
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur est redirigé vers la page d'accueil
        self.assertRedirects(response, reverse('accueil'))

        # Vérifier que la variable de session 'user' n'est pas présente
        self.assertNotIn('user', self.client.session)

        # Vérifier le message de succes
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Vous avez été déconnecter")
