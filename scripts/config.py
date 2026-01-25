from pathlib import Path

# El ID del calendario para Google
CALENDAR_ID = "primary"

# Paths importantes, respectivamente el ROOT, cursoact y el directorio real de cursoact
PARENT_ROOT = Path("~/notas/").expanduser() 
CURSO_ACTUAL_SYMLINK = Path("~/notas/cursoact/").expanduser()
CURSO_ACTUAL_ROOT = CURSO_ACTUAL_SYMLINK.resolve()

# Formato día de la semana abreviado, número del día del mes, mes abreviado, año, horas:minutos
DATE_FORMAT = "%a %d %b %Y %H:%M"
