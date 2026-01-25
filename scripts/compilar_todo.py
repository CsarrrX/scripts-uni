import os
import sys
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from cursos import Cursos

# 1. Configuración de Rutas y Permisos
os.chdir(sys.path[0])
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.file' # Permiso para subir archivos
]

def obtener_servicios():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Si cambiaste los SCOPES (añadiendo Drive), borra el token.pickle viejo
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def subir_o_actualizar(service, ruta_pdf, nombre_drive):
    """Busca el archivo en Drive. Si existe lo actualiza, si no lo crea."""
    media = MediaFileUpload(ruta_pdf, mimetype='application/pdf')
    
    # Buscar si ya existe para no duplicar archivos
    query = f"name = '{nombre_drive}' and trashed = false"
    respuesta = service.files().list(q=query, fields="files(id)").execute()
    archivos = respuesta.get('files', [])

    if archivos:
        file_id = archivos[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"✓ Actualizado en Drive: {nombre_drive}")
    else:
        metadatos = {'name': nombre_drive}
        service.files().create(body=metadatos, media_body=media).execute()
        print(f"+ Creado en Drive: {nombre_drive}")

def main():
    print("Iniciando compilación masiva...")
    drive_service = obtener_servicios()
    mis_cursos = Cursos()

    for curso in mis_cursos:
        print(f"\nProcesando: {curso.info['title']}")
        
        # 2. Tu lógica original de compilación
        clases = curso.clases
        r = clases.parser_clase_range("todas")
        clases.update_clases_master(r)
        clases.compile_master()

        # 3. Localizar el PDF generado (ajusta 'master.pdf' si el nombre varía)
        pdf_local = curso.path / "build" / "master.pdf"
        
        if pdf_local.exists():
            nombre_final = f"Notas_{curso.info['title']}.pdf"
            subir_o_actualizar(drive_service, str(pdf_local), nombre_final)
        else:
            print(f"⚠ No se encontró el PDF en {pdf_local}")

if __name__ == "__main__":
    main()
