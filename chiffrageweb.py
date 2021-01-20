import streamlit as st
import mysql.connector as MC
import pandas as pd
import requests
import json
import csv

class MultiApp:
    """Framework for combining multiple streamlit applications.
    Usage:
        def foo():
            st.title("Hello Foo")
        def bar():
            st.title("Hello Bar")
        app = MultiApp()
        app.add_app("Foo", foo)
        app.add_app("Bar", bar)
        app.run()
    It is also possible keep each application in a separate file.
        import foo
        import bar
        app = MultiApp()
        app.add_app("Foo", foo.app)
        app.add_app("Bar", bar.app)
        app.run()
    """
    def __init__(self):
        self.apps = []

    def add_app(self, title, func):
        """Adds a new application.
        Parameters
        ----------
        func:
            the python function to render this app.
        title:
            title of the app. Appears in the dropdown in the sidebar.
        """
        self.apps.append({
            "title": title,
            "function": func
        })

    def run(self):
        app = st.sidebar.radio(
            'Go To',
            self.apps,
            format_func=lambda app: app['title'])

        app['function']()

def chiffrage():
    # Titre de la page
    st.title('Chiffrage de la collecte pour un prospect')

    # Largeur colonnes
    col1, col2 = st.beta_columns(2)

    # checkbox remorque
    remorque = col1.checkbox('Remorque ?')
    if remorque:
        var_selected_remorque = 1
    else :
        var_selected_remorque = 0

    # checkbox AR
    allerretour = col2.checkbox('Aller-retour ?')
    if allerretour:
        var_selected_ar = 1
    else:
        var_selected_ar = 0

    # connexion à la db mysql gcloud
    connexion = MC.connect(host="34.76.41.24", user="root", password="Dany61211", database="chiffragedb", port=3306)
    curseur = connexion.cursor()

    # Menu déroulant exutoires
    curseur.execute("SELECT name FROM SuezSite ORDER BY name")
    n = 0
    liste_sites_suez = []
    for x in curseur.fetchall():
        liste_sites_suez += [str(x[0])]
        n += 1
    lb_exutoires_idf = st.selectbox("Choisir son site suez :", liste_sites_suez)
    var_selected_exutoire = str(lb_exutoires_idf)

    # Saisie adresse client
    adresse_client = col1.text_input("Adresse client :", "tapez l'adresse")
    var_selected_adresse = str(adresse_client)

    # Menu déroulant CP client
    curseur.execute("SELECT cp_label FROM Cp ORDER BY cp_label")
    n = 0
    liste_cps_idf = []
    for x in curseur.fetchall():
        liste_cps_idf += [str(x[0])]
        n += 1
    lb_cps_idf = col2.selectbox("Choisir le CP client :", liste_cps_idf)
    var_selected_cp = str(lb_cps_idf)

    # Menu déroulant Ville client
    curseur.execute("SELECT city_label FROM City WHERE City.cp_label=%s", (var_selected_cp,))
    n = 0
    liste_villes_idf = []
    for x in curseur.fetchall():
        liste_villes_idf += [str(x[0])]
        n += 1

    lb_villes_idf = col2.selectbox("Choisir la ville client :", liste_villes_idf)
    var_selected_ville = str(lb_villes_idf)

    # calcul
    curseur.execute("SELECT * FROM SuezSite WHERE name=%s", (var_selected_exutoire,))
    mysite = curseur.fetchone()
    origin = str(str(mysite[2]) + ", " + str(mysite[4]) + ", " + mysite[3])
    destination = str(var_selected_adresse + ", " + var_selected_cp + ", " + var_selected_ville)
    donnees = {"units": "metric", "origins": origin, "destinations": destination, "key": "AIzaSyBCHc2dZqiUZbTrDtg0YTJYDgAMx_RYnM8"}
    response = requests.get("https://maps.googleapis.com/maps/api/distancematrix/json", params=donnees)
    result = response.json()
    d = result["rows"][0]["elements"][0]["distance"]["value"]
    d = int(d) # en mètres
    t = result["rows"][0]["elements"][0]["duration"]["value"]
    t = int(t) # en sec
    option_ar = var_selected_ar
    option_rem = var_selected_remorque
    c = 0
    if mysite[5] == "TRI":
        tps_vid = 17
    elif mysite[5] == "K2":
        tps_vid = 20
    elif mysite[5] == "UVE":
        tps_vid = 12
    if option_ar == 0:
        d_cond = d
        tps_cond = t/60
        tps_manip = 20
    elif option_ar == 1:
        d_cond = 2*d
        tps_cond = 2*t / 60
        tps_manip = 12
    if option_rem == 0:
        c = (15 + tps_cond + tps_manip + tps_vid)/60 * 70
    elif option_rem == 1:
        tps_manip = 45
        tps_vid = 35
        c = ((15 + tps_cond + tps_manip + tps_vid)/60 * 70)/2
    st.write("Distance de conduite en Km :", str(round(d_cond/1000, 1)))
    st.write("Temps de conduite en minutes :", str(round(tps_cond, 1)))
    st.write("La collecte d' UNE BENNE coûtera en euros :", str(round(c, 1)))

    # cloture db mysql gcloud
    connexion.close()


def sites_suez():
    # connexion à la db mysql gcloud
    connexion = MC.connect(host="34.76.41.24", user="root", password="Dany61211", database="chiffragedb", port=3306)
    curseur = connexion.cursor()

    # Menu déroulant exutoires
    curseur.execute("SELECT * FROM SuezSite ORDER BY name")

    Noms_s = []
    Adresses_s = []
    Villes_s = []
    CPs_s = []
    Types_s = []
    for elm in curseur.fetchall():
        Noms_s += [elm[1]]
        Adresses_s += [elm[2]]
        Villes_s += [elm[3]]
        CPs_s += [elm[4]]
        Types_s += [elm[5]]

    df_sites = pd.DataFrame({'Nom': Noms_s, 'Adresse': Adresses_s, 'Ville': Villes_s, 'CP': CPs_s, 'Type': Types_s},
                                columns=['Nom', 'Adresse', 'Ville', 'CP', 'Type'])

    st.title('Sites Suez')
    st.write(df_sites)

    st.subheader('Ajouter un site suez en base :')
    # Largeur colonnes
    col1, col2, col3, col4, col5 = st.beta_columns(5)

    # Saisie nouveau site suez
    new_suez_site_name = col1.text_input("Nom du site :", "tapez le nom")
    var_input_site_name = str(new_suez_site_name)

    new_suez_site_address = col2.text_input("Adresse du site :", "tapez l'adresse")
    var_input_site_address = str(new_suez_site_address)

    new_suez_site_cp = col3.text_input("CP du site :", "tapez le code postal")
    var_input_site_cp = str(new_suez_site_cp)

    new_suez_site_ville = col4.text_input("Ville du site :", "tapez la ville")
    var_input_site_ville = str(new_suez_site_ville)

    liste_type = ["TRI", "UVE", "K2"]
    new_suez_site_type = col5.selectbox("Type du site :", liste_type)
    var_input_site_type = str(new_suez_site_type)

    add_new_suez_site = st.button("Ajouter en base")

    if add_new_suez_site:
        curseur.execute("INSERT INTO SuezSite(name,address,city,postcode,type) VALUES(%s,%s,%s,%s,%s)", (var_input_site_name, var_input_site_address, var_input_site_ville, var_input_site_cp, var_input_site_type))
        connexion.commit()

    # cloture db mysql gcloud
    connexion.close()


def villes():
    # connexion à la db mysql gcloud
    connexion = MC.connect(host="34.76.41.24", user="root", password="Dany61211", database="chiffragedb", port=3306)
    curseur = connexion.cursor()

    # Menu déroulant exutoires
    curseur.execute("SELECT * FROM City ORDER BY cp_label")

    CPs_v = []
    Villes_v = []
    for elm in curseur.fetchall():
        CPs_v += [elm[1]]
        Villes_v += [elm[2]]

    df_villes = pd.DataFrame({'CP': CPs_v, 'Ville': Villes_v},columns=['CP', 'Ville'])

    st.title('Villes')
    st.write(df_villes)

    # cloture db mysql gcloud
    connexion.close()


app = MultiApp()
app.add_app("chiffrage", chiffrage)
app.add_app("sites", sites_suez)
app.add_app("villes", villes)
app.run()


