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
import subprocess
from dateutil.parser import parse
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from cursos import Cursos

# Importamos tu configuración personalizada
from config import CALENDAR_ID, CURSO_ACTUAL_SYMLINK

# --- CONFIGURACIÓN ---
os.chdir(sys.path[0])  
cursos = Cursos()
scheduler = sched.scheduler(time.time, time.sleep)
TZ = pytz.timezone("America/Mexico_City")

# Variable global para evitar llamadas excesivas a la API
cache_events = []

def authenticate():
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/drive.file'
    ]
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
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
    
    # Imprimir estado inmediatamente tras activar curso
    print_polybar_status()

def get_events():
    """Descarga los eventos de hoy y los guarda en caché"""
    global cache_events
    try:
        service = authenticate()
        now = datetime.datetime.now(tz=TZ)
        morning = now.replace(hour=0, minute=0, second=0).isoformat()
        evening = now.replace(hour=23, minute=59, second=59).isoformat()

        events_result = service.events().list(
            calendarId=CALENDAR_ID, timeMin=morning, timeMax=evening,
            singleEvents=True, orderBy='startTime'
        ).execute()
        
        cache_events = [{
            'summary': e['summary'],
            'start': parse(e['start']['dateTime']),
            'end': parse(e['end']['dateTime'])
        } for e in events_result.get('items', []) if 'dateTime' in e['start']]
        return cache_events
    except Exception as e:
        # Si falla (ej. sin internet), mantenemos el caché previo
        return cache_events

def print_polybar_status():
    """Imprime texto plano para Polybar (formato no-JSON)"""
    now = datetime.datetime.now(tz=TZ)
    events = cache_events 
    
    current = next((e for e in events if e['start'] < now < e['end']), None)
    
    if current:
        summary = re.sub(r'X[0-9A-Za-z]+', '', current['summary']).strip()
        diff = math.ceil((current['end'] - now).seconds / 60)
        # Icono de clase activa
        txt = f"󰑫 {summary} ({diff}m)"
    else:
        nxt = next((e for e in events if now <= e['start']), None)
        if nxt:
            summary = re.sub(r'X[0-9A-Za-z]+', '', nxt['summary']).strip()
            # Icono de clase próxima
            txt = f"󱪺 Próximo: {summary}"
        else:
            txt = "󱪺 Día libre"

    print(txt, flush=True)

def schedule_updates():
    """Controlador principal del daemon"""
    # Primera carga de datos
    events = get_events()
    now = datetime.datetime.now(tz=TZ)

    for event in events:
        # Programar activación de curso futuro
        if event['start'] > now:
            scheduler.enterabs(event['start'].timestamp(), 1, activate_course, argument=(event,))
        # Activar si ya estamos en horario de clase
        elif event['start'] < now < event['end']:
            activate_course(event)

    # Tarea: Refrescar API cada hora para no saturar
    def refresh_api():
        get_events()
        scheduler.enter(3600, 1, refresh_api)

    # Tarea: Actualizar texto de la barra cada minuto (para el contador m)
    def repeat_status():
        print_polybar_status()
        scheduler.enter(60, 2, repeat_status)
    
    refresh_api()
    repeat_status()
    scheduler.run()

if __name__ == '__main__':
    # Esperamos un poco para asegurar que el sistema cargó el entorno gráfico e internet
    time.sleep(2)
    try:
        schedule_updates()
    except KeyboardInterrupt:
        sys.exit(0)
