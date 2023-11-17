import os
import random
import json
from faker import Faker
import psycopg2

# Configuration de la connexion à la base de données
db_config = {
    'dbname': 'GoldenLine_Serv',
    'user': 'postgres',
    'password': 'ROOT',
    'host': 'localhost',
}

# Création d'une instance Faker
fake = Faker()
   
    
# Connexion à la base de données
conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

# Nombre de lignes à insérer
num_rows = 100  # Vous pouvez ajuster ce nombre en fonction de vos besoins

for i in range(num_rows):
    
    # Génération de données factices
    identifiant_client = fake.unique.random_number()
    nombre_enfants = random.randint(0, 5)
    categorie_socio = fake.random_element(elements=('Etudiant', 'Employe', 'Independant'))
    prix_panier = round(random.uniform(50, 2000), 2)

    

    # Génération de données factices pour la table "collecte"
    montant_alimentaire = round(random.uniform(0, prix_panier), 2)
    montant_multimedia = round(random.uniform(0, prix_panier - montant_alimentaire), 2)
    montant_autre = round(prix_panier - (montant_alimentaire + montant_multimedia), 2)
    
    # Génération de données factices pour le champ Détail_panier au format JSON
    detail_panier = {
    "alimentaire": montant_alimentaire,
    "multimedia": montant_multimedia,
    "autre": montant_autre
    }
    
    # Convertir le dictionnaire en une chaîne JSON
    detail_panier_json = json.dumps(detail_panier)
    

    # Insertion des données dans la table "collecte"
    cursor.execute(
        "INSERT INTO Collecte (Identifiant_Collecte, Detail_panier) VALUES (%s, %s);",
        (i+1, detail_panier_json)
    )
    
    # Insertion des données dans la table "client"
    cursor.execute(
        "INSERT INTO client (identifiant_client, nombre_enfants, categorie_socioprofessionnelle, prix_panier, identifiant_collecte_id) VALUES (%s, %s, %s, %s, %s);",
        (identifiant_client, nombre_enfants, categorie_socio, prix_panier, i+1)
    )

# Validation des modifications
conn.commit()


cursor.close()
conn.close()
