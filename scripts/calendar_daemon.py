import pickle
import os
import sys
import re
import datetime
import json
import math
import time
import sched
import pytz
from dateutil.parser import parse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from cursos import Cursos

from config import CALENDAR_ID, CURSO_ACTUAL_SYMLINK

# --- CONFIGURACIÓN ---
os.chdir(sys.path[0])  # Asegura rutas relativas correctas
cursos = Cursos()
scheduler = sched.scheduler(time.time, time.sleep)
TZ = pytz.timezone("America/Mexico_City") # Ajusta a tu zona

def authenticate():
    SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.file' # Permiso para subir archivos
    ]
    creds = None
    
    # Intenta cargar el token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # Si no hay credenciales válidas, loguearse
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Guardar el token para la próxima vez
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def update_symlink(curso):
    """Actualiza el symlink físico en el sistema"""
    if os.path.islink(CURSO_ACTUAL_SYMLINK) or os.path.exists(CURSO_ACTUAL_SYMLINK):
        os.remove(CURSO_ACTUAL_SYMLINK)
    os.symlink(curso.path, CURSO_ACTUAL_SYMLINK)

def activate_course(event):
    """Busca el curso y actualiza el estado actual"""
    summary = re.sub(r'X[0-9A-Za-z]+', '', event['summary']).strip()
    curso = next((c for c in cursos if c.info['title'].lower() in summary.lower()), None)
    
    if curso:
        cursos.current = curso
        update_symlink(curso)
    
    # Forzamos una actualización inmediata del texto en Waybar
    print_waybar_status()

def get_events():
    """Descarga los eventos de hoy"""
    service = authenticate()
    now = datetime.datetime.now(tz=TZ)
    morning = now.replace(hour=0, minute=0, second=0).isoformat()
    evening = now.replace(hour=23, minute=59, second=59).isoformat()

    events_result = service.events().list(
        calendarId=CALENDAR_ID, timeMin=morning, timeMax=evening,
        singleEvents=True, orderBy='startTime'
    ).execute()
    
    return [{
        'summary': e['summary'],
        'start': parse(e['start']['dateTime']),
        'end': parse(e['end']['dateTime'])
    } for e in events_result.get('items', []) if 'dateTime' in e['start']]

def print_waybar_status():
    """Calcula y escupe el JSON que lee Waybar"""
    now = datetime.datetime.now(tz=TZ)
    # Volvemos a obtener eventos localmente para no pasar variables globales complejas
    events = get_events() 
    
    current = next((e for e in events if e['start'] < now < e['end']), None)
    
    if current:
        summary = re.sub(r'X[0-9A-Za-z]+', '', current['summary']).strip()
        diff = math.ceil((current['end'] - now).seconds / 60)
        txt = f"󰑫 {summary} ({diff}m)"
    else:
        nxt = next((e for e in events if now <= e['start']), None)
        if nxt:
            summary = re.sub(r'X[0-9A-Za-z]+', '', nxt['summary']).strip()
            txt = f"󱪺 Próximo: {summary}"
        else:
            txt = "󱪺 Día libre"

    print(json.dumps({"text": txt, "class": "calendar"}), flush=True)

def schedule_updates():
    """Programa las tareas del día"""
    events = get_events()
    now = datetime.datetime.now(tz=TZ)

    for event in events:
        # Programar activación de symlink cuando empiece la clase
        if event['start'] > now:
            scheduler.enterabs(event['start'].timestamp(), 1, activate_course, argument=(event,))
        
        # Si ya estamos en clase al abrir el script, activarlo de una vez
        elif event['start'] < now < event['end']:
            activate_course(event)

    # Programar que el texto de la barra se actualice cada minuto
    def repeat_status():
        print_waybar_status()
        scheduler.enter(60, 2, repeat_status)
    
    repeat_status()
    scheduler.run()

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    while True:
        try:
            schedule_updates()
        except Exception as e:
            time.sleep(10) 
            continue
