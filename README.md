# Scripts Notes

Este repositorio contiene un conjunto de scripts en Python diseñados para automatizar y gestionar el flujo de trabajo de toma de notas en LaTeX para cursos universitarios. El sistema integra la gestión de archivos locales con Google Calendar (para cambio de contexto automático) y Google Drive (para respaldo de PDFs compilados).

## Dependencias

El sistema requiere las siguientes herramientas y librerías:

### Sistema
- **Python 3.x**
- **LaTeX** (específicamente `latexmk` para la compilación automática)
- **Neovim** (`nvim`): Editor de texto predeterminado para las notas.
- **Kitty**: Emulador de terminal usado para abrir las sesiones de edición.
- **Rofi**: Menú dinámico para X11, usado como interfaz gráfica de selección.
- **Zsh**: Shell utilizada en los comandos de subproceso.

### Python
Las dependencias de Python incluyen:
- `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`: Para la API de Google (Drive y Calendar).
- `PyYAML`: Para leer archivos de configuración `info.yaml`.
- `pytz`, `python-dateutil`: Manejo de zonas horarias y parseo de fechas.

