import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import tkinter as tk
import helper

app_key = '57zf7o2ooz897ti'
app_secret = 'd4edrqdiof5bz0h'
server_addr = "localhost"
server_port = 8090
redirect_uri = "http://" + server_addr + ":" + str(server_port)

class Dropbox:
    _access_token = ""
    _path = "/"
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print(peticion)

        primera_linea = peticion.decode('UTF8').split('\n')[0]
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print("\tauth_code: " + auth_code)

        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"

        client_connection.sendall(http_response.encode())
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        base_uria = "https://www.dropbox.com/oauth2/authorize"
        parametroak = {
            "client_id": app_key,
            "response_type": "code",
            "redirect_uri": redirect_uri
        }
        parametroak_form = urllib.parse.urlencode(parametroak)
        uria = base_uria + "?" + parametroak_form
        print("Dropbox-en baimena emateko nabigatzailea irekitzen......")
        webbrowser.open(uria)

        auth_code = self.local_server()
        print("auth_code: " + auth_code)

        token_url = "https://api.dropboxapi.com/oauth2/token"
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        edukia = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'client_id': app_key,
            'client_secret': app_secret,
            'redirect_uri': redirect_uri
        }
        edukia_form = urllib.parse.urlencode(edukia)
        goiburuak['Content-Length'] = str(len(edukia_form))
        erantzuna = requests.post(token_url, headers=goiburuak, data=edukia_form, allow_redirects=False)
        token_json = erantzuna.json()
        print("Estatusa", erantzuna.status_code)
        print("token_json", token_json)

        self._access_token = token_json["access_token"]
        print("access_token: " + self._access_token)
        self._root.destroy()

    # ------------------------------------------------------------------
    # Metodo interno: obtener entradas de una carpeta de Dropbox
    # ------------------------------------------------------------------
    def _get_folder_entries(self, path):
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }
        edukia = {'path': path if path != '/' else '', 'recursive': False}
        edukia_json = json.dumps(edukia)
        goiburuak['Content-Length'] = str(len(edukia_json))

        erantzuna = requests.post(uri, headers=goiburuak, data=edukia_json, allow_redirects=False)
        edukia_json = json.loads(erantzuna.text)
        guztiak = edukia_json.get('entries', [])

        while edukia_json.get('has_more', False):
            uri_continue = 'https://api.dropboxapi.com/2/files/list_folder/continue'
            datuak_continue = json.dumps({'cursor': edukia_json['cursor']})
            erantzuna = requests.post(uri_continue, headers=goiburuak, data=datuak_continue, allow_redirects=False)
            edukia_json = json.loads(erantzuna.text)
            guztiak += edukia_json.get('entries', [])

        return guztiak

    def list_folder(self, msg_listbox):
        print("/list_folder")
        entries = self._get_folder_entries(self._path)
        contenido_json = {'entries': entries}
        self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)

    def transfer_file(self, file_path, file_data):
        print("/upload")
        uri = 'https://content.dropboxapi.com/2/files/upload'
        dropboxAPIArg = {
            'path': file_path,
            'mode': 'add',
            'autorename': True,
            'mute': False,
            'strict_conflict': False
        }
        dropboxAPIArg_json = json.dumps(dropboxAPIArg)
        goiburuak = {
            'Host': 'content.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': dropboxAPIArg_json,
            'Content-Length': str(len(file_data))
        }
        erantzuna = requests.post(uri, headers=goiburuak, data=file_data, allow_redirects=False)
        print("\tEstatusa: " + str(erantzuna.status_code))
        print("\tDeskribapena: " + str(erantzuna.content))

    def delete_file(self, file_path):
        print("/delete_file")
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }
        edukia = {'path': file_path}
        edukia_json = json.dumps(edukia)
        goiburuak['Content-Length'] = str(len(edukia_json))
        erantzuna = requests.post(uri, headers=goiburuak, data=edukia_json, allow_redirects=False)
        print('Estatusa: ' + str(erantzuna.status_code))
        print("\tDeskribapena: " + str(erantzuna.content))

    def create_folder(self, path):
        print("/create_folder")
        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }
        edukia = {'path': path, 'autorename': False}
        edukia_json = json.dumps(edukia)
        goiburuak['Content-Length'] = str(len(edukia_json))
        erantzuna = requests.post(uri, headers=goiburuak, data=edukia_json, allow_redirects=False)
        print('Estatusa: ' + str(erantzuna.status_code))
        print("\tDeskribapena: " + str(erantzuna.content))

    # ------------------------------------------------------------------
    # Dialogo para elegir carpeta destino (usado por move y copy)
    # ------------------------------------------------------------------
    def _pick_folder(self, parent_window, title="Select destination folder"):
        """
        Abre un popup navegable con las carpetas de Dropbox.
        Devuelve la ruta de la carpeta elegida (str) o None si se cancela.
        Doble clic en una carpeta entra en ella; doble clic en '..' sube un nivel.
        El boton 'Select this folder' confirma la carpeta actual como destino.
        """
        result = {'path': None}
        current = ['/']

        popup = tk.Toplevel(parent_window)
        popup.title(title)
        popup.geometry('360x320')
        popup.iconbitmap('./favicon.ico')
        helper.center(popup)
        popup.grab_set()  # modal: bloquea la ventana principal

        var_path = tk.StringVar(value='/')
        lbl = tk.Label(popup, textvariable=var_path, anchor='w', relief='sunken', padx=4)
        lbl.pack(fill=tk.X, padx=8, pady=(8, 0))

        frame_lb = tk.Frame(popup)
        frame_lb.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        sb = tk.Scrollbar(frame_lb)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb = tk.Listbox(frame_lb, yscrollcommand=sb.set, selectmode=tk.SINGLE)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=lb.yview)

        def load_path(path):
            lb.delete(0, tk.END)
            current[0] = path
            var_path.set(path)
            if path != '/':
                lb.insert(tk.END, '..')
                lb.itemconfigure(tk.END, background='#C6185C', foreground='white')
            entries = self._get_folder_entries(path)
            for e in entries:
                if e['.tag'] == 'folder':
                    lb.insert(tk.END, e['name'])
                    lb.itemconfigure(tk.END, background='#7C86FF', foreground='white')

        def on_double_click(event):
            import os
            sel = lb.curselection()
            if not sel:
                return
            name = lb.get(sel[0])
            if name == '..':
                parent, _ = os.path.split(current[0])
                load_path(parent if parent else '/')
            else:
                new_path = current[0].rstrip('/') + '/' + name
                load_path(new_path)

        lb.bind('<Double-Button-1>', on_double_click)

        frame_btn = tk.Frame(popup)
        frame_btn.pack(fill=tk.X, padx=8, pady=(0, 8))

        tk.Button(frame_btn, text="Select this folder", background='#228B22', fg='white',
                  command=lambda: [result.update({'path': current[0]}), popup.destroy()]
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        tk.Button(frame_btn, text="Cancel", background='#C6185C', fg='white',
                  command=popup.destroy
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X)

        load_path('/')
        popup.wait_window()
        return result['path']

    def move_file(self, from_path, parent_window):
        """
        Abre el dialogo de seleccion de carpeta y mueve from_path al destino elegido,
        manteniendo el nombre original del fichero.
        """
        to_folder = self._pick_folder(parent_window, title="Move to...")
        if to_folder is None:
            return
        print("/move_file")
        uri = 'https://api.dropboxapi.com/2/files/move_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-move_v2
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }
        file_name = from_path.split('/')[-1]
        to_path = to_folder.rstrip('/') + '/' + file_name
        datuak = {'from_path': from_path, 'to_path': to_path, 'autorename': True}
        datuak_json = json.dumps(datuak)
        goiburuak['Content-Length'] = str(len(datuak_json))
        erantzuna = requests.post(uri, headers=goiburuak, data=datuak_json, allow_redirects=False)
        print('\tEstatusa: ' + str(erantzuna.status_code))
        print('\tDeskribapena: ' + str(erantzuna.content))

    def copy_file(self, from_path, parent_window):
        """
        Abre el dialogo de seleccion de carpeta y copia from_path al destino elegido,
        manteniendo el nombre original del fichero.
        """
        to_folder = self._pick_folder(parent_window, title="Copy to...")
        if to_folder is None:
            return
        print("/copy_file")
        uri = 'https://api.dropboxapi.com/2/files/copy_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-copy_v2
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }
        file_name = from_path.split('/')[-1]
        to_path = to_folder.rstrip('/') + '/' + file_name
        datuak = {'from_path': from_path, 'to_path': to_path, 'autorename': True}
        datuak_json = json.dumps(datuak)
        goiburuak['Content-Length'] = str(len(datuak_json))
        erantzuna = requests.post(uri, headers=goiburuak, data=datuak_json, allow_redirects=False)
        print('\tEstatusa: ' + str(erantzuna.status_code))
        print('\tDeskribapena: ' + str(erantzuna.content))

    def search_files(self, query, msg_listbox):
        """
        Filtro LOCAL sobre self._files ya cargados.
        Muestra solo los ficheros cuyo nombre contenga 'query' (case-insensitive).
        Si query esta vacio, restaura la lista completa.
        """
        print("/search_files (local filter): " + query)
        msg_listbox.delete(0, tk.END)

        if not query.strip():
            # Sin filtro: recargar lista completa
            contenido_json = {'entries': self._files}
            self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)
            return

        q = query.lower()
        filtered = [f for f in self._files if q in f['name'].lower()]

        if self._path != '/':
            msg_listbox.insert(tk.END, "..")
            msg_listbox.itemconfigure(tk.END, background="#C6185C", foreground='white')

        for f in filtered:
            msg_listbox.insert(tk.END, f['name'])
            if f['.tag'] == 'folder':
                msg_listbox.itemconfigure(tk.END, background="#7C86FF", foreground='white')

        print('\tResultados encontrados: ' + str(len(filtered)))