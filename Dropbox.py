import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper

app_key = '76svyfxh10f8e3b'
app_secret = 'lh90c8s335l7yu5'
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
        # por el puerto 8090 esta escuchando el servidor que generamos
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        # recibe la redireccio 302 del navegador
        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print (peticion)

        # buscar en solicitud el "auth_code"
        primera_linea =peticion.decode('UTF8').split('\n')[0]
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print ("\tauth_code: " + auth_code)

        # devolver una respuesta al usuario
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"

        #client_connection.sendall(http_response)
        client_connection.sendall(http_response.encode())
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        #############################################
        # RELLENAR CON CODIGO DE LAS PETICIONES HTTP
        # Y PROCESAMIENTO DE LAS RESPUESTAS HTTP
        # PARA LA OBTENCION DEL ACCESS TOKEN
        #############################################

        # 1. PASO: Autorización URL construitu eta nabigatzailea ireki
        auth_url = "https://www.dropbox.com/oauth2/authorize"
        params = {
            "client_id": app_key,
            "response_type": "code",
            "redirect_uri": redirect_uri
        }
        full_url = auth_url + "?" + urllib.parse.urlencode(params)
        print("Opening browser for Dropbox authorization...")
        webbrowser.open(full_url)

        # 2. PASO: auth_code lortu tokiko zerbitzaritik
        auth_code = self.local_server()
        print("auth_code received: " + auth_code)

        # 3. PASO: auth_code trukatu access_token-engatik
        token_url = "https://api.dropboxapi.com/oauth2/token"
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        datuak = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'client_id': app_key,
            'client_secret': app_secret,
            'redirect_uri': redirect_uri
        }
        datuak_form = urllib.parse.urlencode(datuak)  # edukia inprimaki formatudun katean kodifikatu
        goiburuak['Content-Length'] = str(len(datuak_form))  # goiburuak eguneratzen ditugu
        erantzuna = requests.post(token_url, headers=goiburuak, data=datuak_form, allow_redirects=False)
        status = erantzuna.status_code
        token_json = erantzuna.json()
        print("Statusa", status)
        print("token_json", token_json)

        # 4. PASO: access_token gorde
        self._access_token = token_json["access_token"]
        print("access_token: " + self._access_token)

        self._root.destroy()

    def list_folder(self, msg_listbox):
        print("/list_folder")
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-list_folder
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }
        path = "" if self._path == "/" else self._path
        datuak = {'path': path,
                  'recursive': False}
        datuak_json = json.dumps(datuak)
        goiburuak['Content-Length'] = str(len(datuak_json))

        erantzuna = requests.post(uri, headers=goiburuak, data=datuak_json, allow_redirects=False)
        status = erantzuna.status_code
        print("\tStatus: " + str(status))
        edukia_json = json.loads(erantzuna.text)

        guztiak = edukia_json['entries']

        while edukia_json['has_more']:
            uri_continue = 'https://api.dropboxapi.com/2/files/list_folder/continue'
            datuak_continue = json.dumps({'cursor': edukia_json['cursor']})
            erantzuna = requests.post(uri_continue, headers=goiburuak, data=datuak_continue, allow_redirects=False)
            edukia_json = json.loads(erantzuna.text)
            guztiak += edukia_json['entries']

        contenido_json = {'entries': guztiak}
        self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)

    def transfer_file(self, file_path, file_data):
        print("/upload")
        uri = 'https://content.dropboxapi.com/2/files/upload'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-upload
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        dropboxAPIArg = {
            'path': file_path,
            'mode': 'add',
            'autorename': True,
            'mute': False,
            'strict_conflict': False
        }
        dropboxAPIArg_json = json.dumps(dropboxAPIArg)

        goiburuak = {
            'Host' : 'content.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': dropboxAPIArg_json,
            'Content-Length': str(len(file_data))
        }

        erantzuna = requests.post(uri, headers=goiburuak, data=file_data, allow_redirects=False)
        status = erantzuna.status_code
        deskribapena = erantzuna.content
        print("\tStatus: " + str(status))
        print("\tDeskribapena: " + str(deskribapena))

    def delete_file(self, file_path):
        print("/delete_file")
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-delete
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }
        datuak = {'path': file_path}
        datuak_json = json.dumps(datuak)
        goiburuak['Content-Length'] = str(len(datuak_json))

        erantzuna = requests.post(uri, headers=goiburuak, data=datuak_json, allow_redirects=False)
        status = erantzuna.status_code
        deskribapena = erantzuna.content
        print('Status: ' + str(status))
        print("\tDeskribapena: " + str(deskribapena))

    def create_folder(self, path):
        print("/create_folder")
        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-create_folder
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        goiburuak = {
            'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }
        datuak = {'path': path,
                  'autorename': False}
        datuak_json = json.dumps(datuak)
        goiburuak['Content-Length'] = str(len(datuak_json))

        erantzuna = requests.post(uri, headers=goiburuak, data=datuak_json, allow_redirects=False)
        status = erantzuna.status_code
        deskribapena = erantzuna.content
        print('Status: ' + str(status))
        print("\tDeskribapena: " + str(deskribapena))
