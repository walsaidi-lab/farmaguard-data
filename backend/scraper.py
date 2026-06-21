#!/usr/bin/env python3
"""FarmaGuard - scraper des pharmacies de garde.

Recupere chaque jour la liste des pharmacies de garde (annuaire-gratuit.ma)
pour Casablanca, Rabat, Meknes et genere pharmacies.json consomme par l'app.

Champs reels : nom, ville, quartier, adresse, garde.
Coordonnees : approximatives au niveau du quartier (la source n'a pas de GPS).
Telephone : masque a la source -> laisse vide.
"""
import datetime
import json
import re
import sys

import requests
from bs4 import BeautifulSoup

CITIES = {
    "Casablanca": "https://www.annuaire-gratuit.ma/pharmacie-garde-casablanca.html",
    "Rabat": "https://www.annuaire-gratuit.ma/pharmacie-garde-rabat.html",
    "Meknes": "https://www.annuaire-gratuit.ma/pharmacie-garde-meknes.html",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FarmaGuardBot/1.0"}

COORDS = {
    "Casablanca": [
        (["ain chock", "ain chok"], 33.5400, -7.5790),
        (["ain sebaa"], 33.6050, -7.5350),
        (["azhar"], 33.5600, -7.5520),
        (["anassi"], 33.5760, -7.5160),
        (["roches noires", "belv"], 33.5850, -7.5760),
        (["fida", "mers sultan", "bourgogne", "centre"], 33.5830, -7.6080),
        (["oulfa"], 33.5430, -7.6560),
        (["hassani"], 33.5560, -7.6650),
        (["mohammadi"], 33.5900, -7.5650),
        (["lissasfa"], 33.5300, -7.6760),
        (["maarif"], 33.5870, -7.6320),
        (["sbata"], 33.5650, -7.5900),
        (["bernoussi"], 33.6150, -7.5150),
        (["sidi maarouf", "maarouf"], 33.5050, -7.6300),
        (["sidi moumen", "moumen"], 33.5860, -7.5260),
    ],
    "Rabat": [
        (["agdal"], 33.9930, -6.8500),
        (["akkari", "ocean"], 34.0120, -6.8420),
        (["centre"], 34.0140, -6.8330),
        (["medina"], 34.0250, -6.8370),
        (["takadoum", "souissi"], 33.9760, -6.8180),
        (["yacoub", "mansour"], 33.9650, -6.8620),
    ],
    "Meknes": [
        (["ismailia"], 33.8950, -5.5500),
        (["menzeh"], 33.8780, -5.5650),
        (["ouislane"], 33.9150, -5.5250),
        (["toulal"], 33.8600, -5.6050),
    ],
}
CITY_CENTER = {
    "Casablanca": (33.5731, -7.5898),
    "Rabat": (34.0209, -6.8416),
    "Meknes": (33.8950, -5.5500),
}


def resolve_coords(ville, quartier, i):
    q = (quartier or "").lower()
    lat, lng = CITY_CENTER[ville]
    for keys, la, ln in COORDS.get(ville, []):
        if any(k in q for k in keys):
            lat, lng = la, ln
            break
    lat += ((i % 7) - 3) * 0.0012
    lng += ((i % 5) - 2) * 0.0012
    return round(lat, 5), round(lng, 5)


def normalize_garde(text):
    t = (text or "").lower()
    if "24" in t or "permanence" in t or "toute la journ" in t:
        return "24h"
    if "nuit" in t:
        return "nuit"
    return "jour"


def clean_address(addr, nom):
    addr = re.sub(r"\s+", " ", addr or "").strip()
    if nom and addr.lower().startswith(nom.lower()):
        addr = addr[len(nom):].lstrip(" ,.")
    return addr


def scrape_city(ville, url):
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select("li.ag_pharmacy_card")
    result = []
    for i, card in enumerate(cards):
        name_el = card.select_one("h3[itemprop=name]")
        if not name_el:
            continue
        nom = name_el.get_text(strip=True)
        garde_el = card.select_one(".garde-openingStatus")
        addr_el = card.select_one("p[itemprop=streetAddress]")

        quartier = ""
        for item in card.select(".ag_pharmacy_info_item"):
            label = item.find("span")
            val = item.find("strong")
            if not label or not val:
                continue
            if "quartier" in label.get_text(strip=True).lower():
                quartier = val.get_text(strip=True)
                break

        lat, lng = resolve_coords(ville, quartier, i)
        result.append({
            "nom": nom,
            "ville": ville,
            "quartier": quartier,
            "adresse": clean_address(addr_el.get_text(strip=True) if addr_el else "", nom),
            "tel": "",
            "lat": lat,
            "lng": lng,
            "garde": normalize_garde(garde_el.get_text(strip=True) if garde_el else ""),
        })
    return result


def main():
    all_ph = []
    for ville, url in CITIES.items():
        try:
            rows = scrape_city(ville, url)
            print(f"{ville}: {len(rows)} pharmacies", file=sys.stderr)
            all_ph.extend(rows)
        except Exception as e:
            print(f"ERREUR {ville}: {e}", file=sys.stderr)

    data = {
        "source": "annuaire-gratuit.ma",
        "date": datetime.date.today().isoformat(),
        "note": "Donnees de garde du jour. Coordonnees approximatives (quartier). Telephones a completer depuis la source officielle.",
        "pharmacies": all_ph,
    }
    with open("pharmacies.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"TOTAL: {len(all_ph)} pharmacies -> pharmacies.json", file=sys.stderr)
    if not all_ph:
        sys.exit(1)  # echec : ne pas ecraser avec du vide


if __name__ == "__main__":
    main()
