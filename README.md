# Scripts Notes

Este repositorio contiene un conjunto de scripts en Python diseñados para automatizar y gestionar el flujo de trabajo de toma de notas en LaTeX para cursos universitarios. El sistema integra la gestión de archivos locales con Google Calendar (para cambio de contexto automático) y Google Drive (para respaldo de PDFs compilados).

## Dependencias

El sistema requiere las siguientes herramientas y librerías:

### Sistema
- **Python 3.x**
- **LaTeX** (específicamente `latexmk` para la compilación automática)
- **Neovim** (`nvim`): Editor de texto predeterminado para las notas.
- **Kitty**: Emulador de terminal usado para abrir las sesiones de edición.
- **Wofi**: Menú dinámico para Wayland, usado como interfaz gráfica de selección.
- **Zsh**: Shell utilizada en los comandos de subproceso.

### Python
Las dependencias de Python incluyen:
- `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`: Para la API de Google (Drive y Calendar).
- `PyYAML`: Para leer archivos de configuración `info.yaml`.
- `pytz`, `python-dateutil`: Manejo de zonas horarias y parseo de fechas.

## Estructura del Proyecto

La lógica principal se encuentra en el directorio `scripts/`. A continuación se detalla la función de cada archivo y sus componentes.

### `scripts/clases.py`
Este módulo maneja la lógica de bajo nivel de los archivos de notas individuales y su compilación.

*   **Funciones Helper**:
    *   `num_a_file(n)`: Convierte un entero `n` a `clase_NN.tex`.
    *   `file_a_num(s)`: Extrae el entero `NN` del nombre del archivo.

*   **Clase `Clase`**:
    *   Representa un archivo `.tex` individual.
    *   **`__init__`**: Abre el archivo y parsea la metadata (número de clase, fecha, título) usando expresiones regulares (`re`).
    *   **`editar()`**: Abre una nueva instancia de `kitty` ejecutando `nvim` sobre el archivo de la nota.

*   **Clase `Clases(list)`**:
    *   Hereda de `list` y actúa como una colección de objetos `Clase` para un curso específico.
    *   **`read_files()`**: Escanea el directorio del curso buscando archivos `clase_*.tex` y puebla la lista.
    *   **`parser_clase_spec(string)`**: Interpreta strings como "ultima", "previa" o números para identificar notas específicas.
    *   **`parser_clase_range(arg)`**: Genera rangos de clases (ej. "1-5", "todas") para compilar selecciones parciales.
    *   **`update_clases_master(r)`**: Modifica dinámicamente el archivo `master.tex` del curso (insertando los `\input{...}` correspondientes) basándose en el rango seleccionado. Mantiene el preámbulo y el cierre del documento intactos detectando los marcadores "% inicio clases" y "% fin clases".
    *   **`nueva_clase()`**: Crea un nuevo archivo `.tex` con la fecha actual y el número consecutivo siguiente. Actualiza el `master.tex` para incluir la nota nueva y la anterior (para contexto) y la abre para edición.
    *   **`compile_master()`**: Ejecuta `latexmk` en modo silencioso (`-interaction=nonstopmode`) para generar el PDF.

### `scripts/cursos.py`
Maneja la abstracción de los cursos y la navegación entre ellos.

*   **Clase `Curso`**:
    *   Representa un directorio de curso.
    *   Carga la metadata desde `info.yaml` (título, abreviación, etc.).
    *   Utiliza *lazy loading* para instanciar el objeto `Clases` asociado solo cuando es necesario.

*   **Clase `Cursos(list)`**:
    *   Escanea el directorio raíz (`PARENT_ROOT`) para descubrir todos los cursos disponibles.
    *   **Propiedad `current`**: Gestiona un enlace simbólico (`symlink`) que apunta al curso "activo". Esto permite acceder rápidamente a las notas del curso actual desde otros scripts o la terminal.

### `scripts/wofi_link.py`
Provee una interfaz gráfica rápida (GUI) utilizando `wofi`.

*   **Flujo Principal**:
    1.  Despliega una lista de cursos disponibles.
    2.  Al seleccionar un curso, ofrece acciones: "Nueva nota", "Compilar master", "Editar una nota", "Compilar todo (drive)".
    3.  Ejecuta la lógica correspondiente llamando a los métodos de `Clases` (ej. crear nota, actualizar master, compilar).

### `scripts/calendar_daemon.py`
Servicio en segundo plano para la automatización contextual.

*   **`activate_course(event)`**: Recibe un evento de calendario, busca si coincide con algún curso registrado y actualiza el symlink del curso actual (`Cursos.current`).
*   **`get_events()`**: Consulta la API de Google Calendar para obtener los eventos del día actual.
*   **Integración Waybar**: Imprime el estado actual en formato JSON para ser consumido por módulos de Waybar.

### `scripts/compilar_todo.py`
Script de mantenimiento y respaldo.

*   Itera sobre todos los cursos disponibles.
*   Compila el documento maestro (`master.tex`) incluyendo **todas** las notas.
*   Sube o actualiza el PDF resultante en Google Drive, verificando si el archivo ya existe para evitar duplicados.

### `scripts/config.py`
Archivo central de configuración. Define rutas absolutas (`PARENT_ROOT`, `CURSO_ACTUAL_SYMLINK`), formatos de fecha y IDs de calendario.

### `scripts/iniciar-cursos.py`
Script utilitario para inicializar la estructura de directorios y archivos base (`master.tex`) para nuevos cursos.

### `preamble.tex`
Archivo LaTeX raíz que contiene la configuración de paquetes, macros y estilos comunes para todos los documentos. Es importado por los archivos `master.tex` de cada curso.

## Integración con Google Services

El sistema utiliza `google-auth` con un flujo de credenciales OAuth 2.0.
*   Requiere un archivo `credentials.json` en el directorio de scripts.
*   Genera y almacena un `token.pickle` localmente para mantener la sesión activa sin re-autenticación constante.
*   **Scopes utilizados**:
    *   `calendar.readonly`: Para leer horarios y cambiar el contexto automáticamente.
    *   `drive.file`: Para subir y actualizar únicamente los archivos creados por el script (los PDFs de notas).