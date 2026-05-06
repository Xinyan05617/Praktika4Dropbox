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

        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("##### 1. PETICION #####")
        metodo = 'GET'
        uri = "https://egela.ehu.eus/login/index.php"
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        goiburuak1 = {'Host': 'egela.ehu.eus'}
        erantzuna1 = requests.get(uri, headers=goiburuak1, allow_redirects=False)

        set_cookie = erantzuna1.headers.get("Set-Cookie", "")
        self._cookie = set_cookie.split(";")[0]

        soup = BeautifulSoup(erantzuna1.content, "html.parser")
        logintoken_input = soup.find("input", {"name": "logintoken"})
        logintoken = logintoken_input['value']

        print(f"Cookie: {self._cookie}")
        print(f"logintoken: {logintoken}")

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 2. PETICION #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        goiburuak2 = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        edukia = {
            "username": username,
            "password": password,
            "logintoken": logintoken
        }
        edukia_encoded = urllib.parse.urlencode(edukia)
        goiburuak2['Content-Length'] = str(len(edukia_encoded))

        erantzuna2 = requests.post(uri, headers=goiburuak2, data=edukia_encoded, allow_redirects=False)

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
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        goiburuak3 = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,
        }
        erantzuna3 = requests.get(location2, headers=goiburuak3, allow_redirects=False)
        location3 = erantzuna3.headers.get('Location', '')
        print(f"Status: {erantzuna3.status_code}, Location: {location3}")

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        print("\n##### 4. PETICION #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        goiburuak4 = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,
        }
        erantzuna4 = requests.get(location3, headers=goiburuak4, allow_redirects=False)
        print(f"Status: {erantzuna4.status_code}")

        # Login egiaztatu
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
            #############################################
            # ACTUALIZAR VARIABLES
            #############################################
            soup4 = BeautifulSoup(erantzuna4.content, "html.parser")
            for link in soup4.find_all("a"):
                text = link.text.strip()
                if "Web" in text and "Sistem" in text:
                    self._curso = link.get("href")
                    break

            self._login = 1
            self._root.destroy()
        else:
            messagebox.showinfo("Alert Message", "Login incorrect!")

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("\n##### 4. PETICION (Página principal de la asignatura en eGela) #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        goiburuak = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,
        }
        erantzuna = requests.get(self._curso, headers=goiburuak, allow_redirects=False)
        soup = BeautifulSoup(erantzuna.content, "html.parser")

        # Erlaitza guztiak bilatu (Practica 2ko eskaera5 bezala)
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

            # Erlaitzaren HTMLa lortu
            erantzuna_erlaitza = requests.get(href, headers=goiburuak, allow_redirects=False)
            soup_erlaitza = BeautifulSoup(erantzuna_erlaitza.content, "html.parser")

            # PDF ikonoa duten img tag-ak bilatu
            estekak = soup_erlaitza.find_all('img', class_=['activitycon', 'nofilter'])
            for errenkada in estekak:
                if errenkada['src'].find("/pdf") != -1:
                    blokea = errenkada.find_parent('div', class_=['activitytitle', 'media'])
                    if blokea:
                        a = blokea.find('a')
                        if a:
                            pdf_links_raw.append(a['href'])

        progress_step = float(100.0 / len(pdf_links_raw)) if pdf_links_raw else 100

        print("\n##### Analisis del HTML... #####")
        #############################################
        # ANALISIS DE LA PAGINA DEL AULA EN EGELA
        # PARA BUSCAR PDFs
        #############################################
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

            # INICIALIZA Y ACTUALIZAR BARRA DE PROGRESO
            # POR CADA PDF ANIADIDO EN self._refs
            progress_step = float(100.0 / len(pdf_links_raw))

            progress += progress_step
            progress_var.set(progress)
            progress_bar.update()
            time.sleep(0.1)

        popup.destroy()

        print("\n##### LISTA FINAL DE PDFs #####")
        print(self._refs)

        return self._refs


    def get_pdf(self, selection):
        print("\t##### descargando  PDF... #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        pdf_info = self._refs[selection]
        pdf_name = pdf_info['pdf_name']
        pdf_link = pdf_info['pdf_link']

        goiburuak = {
            'Host': 'egela.ehu.eus',
            'Cookie': self._cookie,
        }
        erantzuna = requests.get(pdf_link, headers=goiburuak, allow_redirects=False)
        pdf_content = erantzuna.content

        print(f"\t PDF deskargatuta: {pdf_name} ({len(pdf_content)} bytes)")

        return pdf_name, pdf_content