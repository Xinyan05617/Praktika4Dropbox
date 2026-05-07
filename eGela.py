# -*- coding: UTF-8 -*-
from tkinter import messagebox
import requests
import urllib
from urllib.parse import unquote
from bs4 import BeautifulSoup
import time
import helper

class eGela:
    _login = 0
    _cookie = ""
    _curso = ""
    _refs = []
    _root = None

    def __init__(self, root):
        self._root = root

    def check_credentials(self, username, password, event=None):
        if hasattr(username, 'get'):
            username = username.get()
        if hasattr(password, 'get'):
            password = password.get()

        # Erabiltzaile-izena edo pasahitza hutsak diren egiaztatu
        if not username.strip() or not password.strip():
            messagebox.showerror("Errorea", "Erabiltzaile-izena eta pasahitza bete behar dira.")
            return

        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("##### 1. PETICION #####")
        uri = "https://egela.ehu.eus/login/index.php"
        goiburuak1 = {
            'Host': 'egela.ehu.eus'  # Zerbitzariaren izena (HTTP/1.1-ek beharrezkoa du)
        }
        erantzuna1 = requests.get(uri, headers=goiburuak1, allow_redirects=False)

        # Cookie-a gorde: hurrengo eskaerak identifikatzeko erabiltzen da
        set_cookie = erantzuna1.headers.get("Set-Cookie", "")
        self._cookie = set_cookie.split(";")[0]

        # logintoken-a atera HTML-tik: CSRF erasoen kontrako babes-token bat da
        soup = BeautifulSoup(erantzuna1.content, "html.parser")
        logintoken_input = soup.find("input", {"name": "logintoken"})
        if not logintoken_input:
            popup.destroy()
            messagebox.showerror("Errorea", "Ezin izan da logintoken-a eskuratu. Saiatu berriro.")
            return
        logintoken = logintoken_input['value']

        print(f"Cookie: {self._cookie}")
        print(f"logintoken: {logintoken}")

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 2. PETICION #####")
        goiburuak2 = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,                               # Aurreko eskaeran jasotako cookie-a
            'Content-Type': 'application/x-www-form-urlencoded', # Formulario-datuak URL-kodetuta bidaltzen dira
        }
        edukia = {
            "username": username,       # Erabiltzaile-izena (NAN edo UPV/EHUko kontu-izena)
            "password": password,       # Pasahitza (testu arrunt gisa bidaltzen da HTTPS-ren bidez)
            "logintoken": logintoken    # CSRF token-a: zerbitzariak eskaera baliozkotzeko erabiltzen du
        }
        edukia_encoded = urllib.parse.urlencode(edukia)
        goiburuak2['Content-Length'] = str(len(edukia_encoded))

        erantzuna2 = requests.post(uri, headers=goiburuak2, data=edukia_encoded, allow_redirects=False)

        # Cookie berria eguneratu (login POST-ak cookie berria eman dezake)
        set_cookie2 = erantzuna2.headers.get("Set-Cookie", "")
        if set_cookie2:
            self._cookie = set_cookie2.split(";")[0]

        location2 = erantzuna2.headers.get('Location', '')
        print(f"Status: {erantzuna2.status_code}, Location: {location2}")

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 3. PETICION #####")
        goiburuak3 = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,  # Autentifikazio-cookie-a: saioa identifikatzeko
        }
        erantzuna3 = requests.get(location2, headers=goiburuak3, allow_redirects=False)
        location3 = erantzuna3.headers.get('Location', '')
        print(f"Status: {erantzuna3.status_code}, Location: {location3}")

        # Login okerra: 3. eskaerak ez du redirect-ik itzultzen (location3 hutsa da)
        # Kredentzialekin arazoa dagoela adierazten du
        if not location3:
            popup.destroy()
            messagebox.showerror("Alert Message", "Login incorrect!")
            return

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        print("\n##### 4. PETICION #####")
        goiburuak4 = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,  # Cookie-a mantendu: saio-hasiera finkatuta dago hemendik aurrera
        }
        erantzuna4 = requests.get(location3, headers=goiburuak4, allow_redirects=False)
        print(f"Status: {erantzuna4.status_code}")

        # Profil-orria eskatu: 200 itzultzen badu login eginda gaude; bestela ez
        # Hau da egiazko egiaztapena: login okerrak 303 redirect itzultzen du
        erantzuna_perfil = requests.get(
            "https://egela.ehu.eus/user/profile.php",
            headers=goiburuak4,
            allow_redirects=False
        )
        COMPROBACION_DE_LOG_IN = (erantzuna_perfil.status_code == 200)

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        if COMPROBACION_DE_LOG_IN:
            # Irakasgaiaren esteka bilatu dashboard-eko HTML-tik
            soup4 = BeautifulSoup(erantzuna4.content, "html.parser")
            for link in soup4.find_all("a"):
                text = link.text.strip()
                if "Web" in text and "Sistem" in text:
                    self._curso = link.get("href")
                    break

            if not self._curso:
                messagebox.showwarning("Oharra", "Login eginda baina irakasgaiaren esteka ez da aurkitu.")
                return

            self._login = 1
            self._root.destroy()
        else:
            messagebox.showerror("Alert Message", "Login incorrect!")

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("\n##### PETICION (Irakasgaiaren orri nagusia eGela-n) #####")
        goiburuak = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,  # Saio-cookie-a: autentifikatutako eskaera egiteko
        }
        erantzuna = requests.get(self._curso, headers=goiburuak, allow_redirects=False)
        soup = BeautifulSoup(erantzuna.content, "html.parser")

        pdf_links_raw = []
        seen_pdf_names = set()
        li_list = soup.find_all("li", class_="nav-item")
        for li in li_list:
            a_tag = li.find("a", class_="nav-link")
            if not a_tag:
                continue
            href = a_tag.get("href")
            if not href or href == "#":
                continue

            erantzuna_erlaitza = requests.get(href, headers=goiburuak, allow_redirects=False)
            soup_erlaitza = BeautifulSoup(erantzuna_erlaitza.content, "html.parser")

            estekak = soup_erlaitza.find_all('img', class_=['activitycon', 'nofilter'])
            for errenkada in estekak:
                if errenkada['src'].find("/pdf") != -1:
                    blokea = errenkada.find_parent('div', class_=['activitytitle', 'media'])
                    if blokea:
                        a = blokea.find('a')
                        if a:
                            pdf_links_raw.append(a['href'])

        progress_step = float(100.0 / len(pdf_links_raw)) if pdf_links_raw else 100

        print("\n##### HTML-aren analisia... #####")
        self._refs = []
        for uria_pdf in pdf_links_raw:
            erantzuna_pdf = requests.get(uria_pdf, headers=goiburuak, allow_redirects=False)
            soup2 = BeautifulSoup(erantzuna_pdf.content, "html.parser")

            pdf_div = soup2.find('div', {'class': 'resourceworkaround'})
            if not pdf_div:
                continue

            uria_deskargatu = pdf_div.a['href']
            pdf_izena = unquote(uria_deskargatu.split('/')[-1].split('?')[0])

            if pdf_izena in seen_pdf_names:
                continue

            seen_pdf_names.add(pdf_izena)
            self._refs.append({
                'pdf_name': pdf_izena,
                'pdf_link': uria_deskargatu
            })

            progress_step = float(100.0 / len(pdf_links_raw))
            progress += progress_step
            progress_var.set(progress)
            progress_bar.update()
            time.sleep(0.1)

        popup.destroy()

        print("\n##### PDFen azken zerrenda #####")
        print(self._refs)

        return self._refs

    def get_pdf(self, selection):
        print("\t##### PDF deskargatzen... #####")
        pdf_info = self._refs[selection]
        pdf_name = pdf_info['pdf_name']
        pdf_link = pdf_info['pdf_link']

        goiburuak = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,  # Saio-cookie-a: autentifikatutako deskarga egiteko
        }
        erantzuna = requests.get(pdf_link, headers=goiburuak, allow_redirects=False)
        pdf_content = erantzuna.content

        print(f"\t PDF deskargatuta: {pdf_name} ({len(pdf_content)} bytes)")

        return pdf_name, pdf_content