from bs4 import BeautifulSoup
import requests
from InquirerPy import inquirer
import os
import threading
import time
from colorama import Fore, Style, init

# Initialisation colorama
init(autoreset=True)

# =========================
# CONFIGURATION
# =========================
BASE_URL = "https://fr.wikipedia.org"
URL_RANDOM = "/wiki/Sp%C3%A9cial:Page_au_hasard"

DUREE_MAX =  20      # 3 minutes
LIENS_PAR_PAGE = 20

headers = {
    "User-Agent": "Mozilla/5.0 (WikiGame Python)"
}

# =========================
# OUTILS
# =========================
def nettoyer_ecran():
    os.system("cls" if os.name == "nt" else "clear")


def afficher_fin_temps(): 
    nettoyer_ecran()
    print(Fore.RED + """
████████╗███████╗███╗   ███╗██████╗ ███████╗
╚══██╔══╝██╔════╝████╗ ████║██╔══██╗██╔════╝
   ██║   █████╗  ██╔████╔██║██████╔╝███████╗
   ██║   ██╔══╝  ██║╚██╔╝██║██╔═══╝ ╚════██║
   ██║   ███████╗██║ ╚═╝ ██║██║     ███████║
   ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝     ╚══════╝

        ⏱  TEMPS ÉCOULÉ  ⏱
""" + Style.RESET_ALL)


def afficher_victoire():
    nettoyer_ecran()
    print(Fore.GREEN + """
██╗   ██╗██╗ ██████╗████████╗ ██████╗ ██╗██████╗ ███████╗
██║   ██║██║██╔════╝╚══██╔══╝██╔═══██╗██║██╔══██╗██╔════╝
██║   ██║██║██║        ██║   ██║   ██║██║██████╔╝█████╗
╚██╗ ██╔╝██║██║        ██║   ██║   ██║██║██╔══██╗██╔══╝
 ╚████╔╝ ██║╚██████╗   ██║   ╚██████╔╝██║██║  ██║███████╗
  ╚═══╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝
""" + Style.RESET_ALL)


# =========================
# SCRAPING WIKIPEDIA
# =========================
def obtenir_enlaces(url):
    html = requests.get(BASE_URL + url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")

    contenu = soup.find("div", class_="mw-parser-output")
    if contenu is None:
        return {}, "Page non valide", False

    toc = contenu.find("div", class_="toc")
    if toc:
        toc.decompose()

    liens = {}
    compteur = 1

    for link in contenu.find_all("a", href=True):
        href = link["href"]
        if href.startswith("/wiki/") and ":" not in href and link.text.strip():
            liens[compteur] = {
                "texte": link.text.strip(),
                "url": href
            }
            compteur += 1

    titre = soup.title.text.replace(" — Wikipédia", "")
    return liens, titre, True


# =========================
# PAGINATION
# =========================
def generer_options(liens, page):
    total = len(liens)
    total_pages = (total + LIENS_PAR_PAGE - 1) // LIENS_PAR_PAGE

    debut = (page - 1) * LIENS_PAR_PAGE + 1
    fin = min(debut + LIENS_PAR_PAGE - 1, total)

    options = []

    for i in range(debut, fin + 1):
        options.append(f"{i} → {liens[i]['texte']}")

    if page > 1:
        options.append("98 → Page précédente")
    if page < total_pages:
        options.append("99 → Page suivante")

    options.append("q → Quitter")
    return options, total_pages


# =========================
# TIMER (THREAD)
# =========================
def timer_compte_a_rebours(duree, evenement_fin):
    for restant in range(duree, 0, -1):
        mins = restant // 60
        secs = restant % 60
        print(Fore.YELLOW + f"\r⏱ Temps restant : {mins:02d}:{secs:02d}", end="")
        time.sleep(1)
    evenement_fin.set()


# =========================
# INITIALISATION DU JEU
# =========================
# Page cible
_, TITRE_CIBLE, _ = obtenir_enlaces(URL_RANDOM)

# Page de départ
url_courante = URL_RANDOM

historique = []

# Lancer le timer
fin_temps = threading.Event()
threading.Thread(
    target=timer_compte_a_rebours,
    args=(DUREE_MAX, fin_temps),
    daemon=True
).start()

# =========================
# BOUCLE PRINCIPALE
# =========================
while True:
    liens, titre_page, valide = obtenir_enlaces(url_courante)

    if not valide:
        continue

    historique.append(titre_page)

    # ===== VICTOIRE AVANT LA FIN DU TEMPS =====
    if titre_page == TITRE_CIBLE and not fin_temps.is_set():
        afficher_victoire()
        print(Fore.GREEN + "🎉 Félicitations ! Vous avez atteint la page cible AVANT la fin du temps.\n")
        print(f"🎯 Page cible : {TITRE_CIBLE}\n")

        print("Historique des pages visitées :")
        for page in historique:
            print(" -", page)

        print(f"\nNombre de pages parcourues : {len(historique)}")
        input("\nAppuyez sur ENTER pour quitter.")
        break

    page_actuelle = 1

    while True:
        # ===== TEMPS ÉCOULÉ AVANT LA VICTOIRE =====
        if fin_temps.is_set():
            afficher_fin_temps()
            print(Fore.RED + "❌ JEU TERMINÉ : objectif non atteint à temps.\n")
            print(Fore.RED + f"🎯 Page cible : {TITRE_CIBLE}\n")

            print("Historique des pages visitées :")
            for page in historique:
                print(" -", page)

            print(f"\nNombre de pages parcourues : {len(historique)}")
            input("\nAppuyez sur ENTER pour quitter.")
            exit()

        nettoyer_ecran()
        print(Fore.CYAN + f"🎯 Page cible : {TITRE_CIBLE}")
        print(Fore.CYAN + f"📄 Page actuelle : {titre_page}\n")

        options, total_pages = generer_options(liens, page_actuelle)
        print(f"Page {page_actuelle}/{total_pages}\n")

        choix = inquirer.select(
            message="Choisissez un lien :",
            choices=options
        ).execute()

        if choix == "q → Quitter":
            exit()

        elif choix.startswith("98"):
            page_actuelle -= 1

        elif choix.startswith("99"):
            page_actuelle += 1

        else:
            numero = int(choix.split(" → ")[0])
            url_courante = liens[numero]["url"]
            break
