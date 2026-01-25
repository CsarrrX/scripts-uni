import re # Busqueda inteligente
import os # Sistema operativo
import locale # Idioma, fecha, etc...
import subprocess # Para correr paquetes fuera del script
from pathlib import Path # Manejo de paths
from datetime import datetime # Manejo de fechas

# Importamos nuestros configs
from config import PARENT_ROOT, CURSO_ACTUAL_ROOT, CURSO_ACTUAL_SYMLINK, DATE_FORMAT

# Formato de las fechas
locale.setlocale(locale.LC_TIME, "es_ES.utf8") 

# Un par de funciones importantes para generar los archivos clase_NN.tex
def num_a_file(n): # Toma un número y lo convierte a un filename
    return f"clase_{n:02d}.tex"   

def file_a_num(s): # Toma un filename, le quita el .tex, lo divide en clase y NN, y regresa NN como entero
    return int(s.stem.split('_')[-1])

# Primera class importante: Clase
class Clase():
    def __init__(self, file_path, curso): # Le damos un self, un path y un curso
        clase_match = None # Iteramos sobre los archivos para encontrar clases.

        with file_path.open() as f: # Buscador de \clase{}{}{} en los archivos de clase_NN.tex
            for line in f:
                clase_match = re.search(r"clase\{(.*?)\}\{(.*?)\}\{(.*)\}", line)
                if clase_match:
                    break 

        # Caracteristicas de las clases
        if clase_match: 
            fecha_str = clase_match.group(2)
            fecha = datetime.strptime(fecha_str, DATE_FORMAT)
            titulo = clase_match.group(3)
            
            self.file_path = file_path
            self.fecha = fecha
            self.number = int(clase_match.group(1))
            self.titulo = titulo
            self.curso = curso

        def editar(): # Abre una terminal de nvim con el file
            subprocess.Popen([
                "kitty",
                "nvim",
                str(self.file_path)
            ])

        def __str__(self): # Como se ven representadas nuestras clases en strings
            return f"<Clase {self.curso.info['short']} {self.number} {self.titulo}" 

        
# Segunda clase importante: Clases, hereda de lists y sabe auto-llenarse con las Clases
class Clases(list):
    def __init__(self, curso):
        # Rutas importantes
        self.curso = curso
        self.root = curso.path 
        self.master_file = self.root / "master.tex"
        list.__init__(self, self.read_files()) # Hacemos que Clases sea una lista y se llene con la funcion read_files()

    def read_files(self):
        files = self.root.glob("clase_*.tex") # Buscamos todos los archivos clase_NN.tex
        return sorted((Clase(f, self.curso) for f in files), key=lambda l: l.number) # Los regresamos ya organizados

    def parser_clase_spec(self, string): # Parser que regresa el número de lección en base a el string que se da
        if len(self) == 0:
            return 0

        if string.isdigit():
            return int(string)
        elif string == "ultima": # Si escribimos ultima retorna la ultima
            return self[-1].number
        elif string == "previa": # Previa retorna la penultima (la vamos a usar para tener contexto para nuevas)
            return self[-1].number - 1 

    def parser_clase_range(self, arg): # Parser que toma un rango de lecciones y las regresa
        all_numbers = [clase.number for clase in self]
        if "todas" in arg:
            return all_numbers

        if "-" in arg:
            start, end = [self.parser_clase_spec(bit) for bit in arg.split("-")] # Tomamos un inicio y fin separando el arg
            return list(set(all_numbers) & set(range(start, end+1))) # Retornamos la interseccion de nuestras clases y el arg

        return [self.parser_clase_spec(arg)]

    # FUNCION IMPORTANTE: detecta las "partes" del archivo, nos va a servir para incluir algunas de las lectures como queramos 
    @staticmethod
    def get_header_footer(filepath):
        part = 0
        header = ''
        footer = ''
        with filepath.open() as f:
            for line in f:
                if 'fin clases' in line:
                    part = 2

                if part == 0:
                    header += line
                if part == 2:
                    footer += line

                if 'inicio clases' in line:
                    part = 1
        return (header, footer)

    # FUNCION IMPORTANTE: añade un rango r de clases, ese rango r es masticado por el parser
    def update_clases_master(self, r):
        header, footer = self.get_header_footer(self.master_file)
        body = ''.join(' ' * 4 + r'\input{' + num_a_file(number) + '}\n' for number in r)
        self.master_file.write_text(header + body + footer)

    # FUNCION IMPORTANTE: creación de una nueva clase
    def nueva_clase(self):
        if len(self) != 0:
            nueva_clase_number = self[-1].number + 1 # Si el tamaño de la lista de clases no es 0, le damos el número que sigue
        else:
            nueva_clase_number = 1

        nueva_clase_path = self.root / num_a_file(nueva_clase_number) # Path absoluto al file

        fecha = datetime.today().strftime(DATE_FORMAT) # Definimos la fecha para añadirla automaticamente al file 

        nueva_clase_path.touch() # Creamos el archivo
        nueva_clase_path.write_text(f'\\clase{{{nueva_clase_number}}}{{{fecha}}}{{}}\n') # Añadimos nuestro identificador

        # Añadimos las dos ultimas clases
        if nueva_clase_number == 1:
            self.update_clases_master([1])
        else:
            self.update_clases_master([nueva_clase_number - 1, nueva_clase_number])

        # Actualizamos el tamaño de la lista
        self.read_files()

        # Creamos una nueva clase
        l = Clase(nueva_clase_path, self.curso)

        return l

    def compile_master(self):
        result = subprocess.run(
            ['latexmk', '-f', '-interaction=nonstopmode', str(self.master_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(self.root)
        )
        return result.returncode



        
