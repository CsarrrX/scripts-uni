import re
from pathlib import Path

# Configuración de entornos a capturar
ENTORNOS = [
    "theorem", "teorema",
    "lemma", "lema",
    "proposition", "proposicion", "proposición",
    "corollary", "corolario",
    "definition", "definicion", "definición",
    "metodo",
    "ejemplo",
]

def obtener_preambulo_master(curso):
    """
    Lee el master.tex del curso y extrae todo lo previo al begin{document}.
    Esto asegura que el formulario tenga los mismos paquetes y macros que tus notas.
    """
    master_path = curso.path / "master.tex"
    
    if not master_path.exists():
        # Fallback por si acaso no existe master (raro en tu flujo)
        return r"\documentclass{article}\usepackage{amsmath,amsthm,amssymb}\begin{document}"

    contenido = []
    try:
        with open(master_path, 'r', encoding='utf-8') as f:
            for line in f:
                if r'\begin{document}' in line:
                    break
                contenido.append(line)
        
        # Agregamos cosas específicas para el formulario si hacen falta
        # Por ejemplo, asegurarnos que hyperref esté cargado si no lo está
        preambulo = "".join(contenido)
        return preambulo
    except Exception as e:
        print(f"Error leyendo master.tex: {e}")
        return r"\documentclass{article}\begin{document}"

def extraer_bloques(texto):
    """
    Busca bloques begin{env} ... end{env} para los entornos deseados.
    """
    bloques_encontrados = []
    
    # Regex optimizado:
    # 1. \begin{TIPO}
    # 2. (.*?) Contenido (Non-greedy, DOTALL)
    # 3. \end{TIPO}
    patron = r'\\begin\{(' + '|'.join(ENTORNOS) + r')\}(.*?)\\end\{\1\}'
    
    matches = re.finditer(patron, texto, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        env_type = match.group(1)
        body = match.group(2)
        bloque = f"\\begin{{{env_type}}}{body}\\end{{{env_type}}}"
        bloques_encontrados.append(bloque)
        
    return bloques_encontrados

def generar_formulario(curso):
    """
    Genera un archivo 'formulario.tex' en la carpeta del curso.
    """
    print(f"--- Generando formulario para: {curso.name} ---")
    
    # 1. Obtener el preámbulo real de TU master.tex
    preambulo = obtener_preambulo_master(curso)
    
    contenido_body = []
    
    # Título del formulario
    contenido_body.append(f"\\title{{Formulario: {curso.name}}}")
    contenido_body.append(r"\date{\today}")
    contenido_body.append(r"\maketitle")
    contenido_body.append(r"\tableofcontents")
    contenido_body.append(r"\newpage")

    # 2. Iterar usando TU estructura de Clases (ya ordenadas por número)
    # Accedemos a curso.clases.read_files() implícitamente al iterar sobre curso.clases
    # pero como Clases es una lista lazy-loaded en tu código original, hacemos esto:
    
    clases_lista = curso.clases # Esto instancia la clase Clases y lee los archivos
    
    if not clases_lista:
        print("No se encontraron clases en este curso.")
        return

    teoremas_totales = 0

    for clase in clases_lista:
        try:
            # Leemos el archivo clase_NN.tex
            texto = clase.file_path.read_text(encoding='utf-8')
            
            bloques = extraer_bloques(texto)
            
            if bloques:
                # Header bonito para separar clases
                fecha_str = clase.fecha.strftime("%d/%m")
                titulo_seccion = f"Clase {clase.number}: {clase.titulo} ({fecha_str})"
                
                contenido_body.append(f"\n\\section*{{{titulo_seccion}}}")
                # Agregamos los bloques con una linea separadora
                contenido_body.append("\n\\hrulefill\n".join(bloques))
                contenido_body.append(r"\vspace{0.5cm}") # Espacio extra al final de la clase
                
                teoremas_totales += len(bloques)
                print(f"  -> Clase {clase.number}: {len(bloques)} extractos.")
                
        except Exception as e:
            print(f"Error procesando {clase.file_path.name}: {e}")

    # 3. Escribir el archivo final
    contenido_body.append(r"\end{document}")
    
    path_salida = curso.path / "formulario.tex"
    
    full_latex = preambulo + "\n" + r"\begin{document}" + "\n" + "\n".join(contenido_body)
    
    path_salida.write_text(full_latex, encoding='utf-8')
    
    print(f"Terminado. {teoremas_totales} elementos guardados en {path_salida.name}")
