from pathlib import Path
import yaml # YAML para poder leer las info.yaml de cada curso

from clases import Clases 
from config import PARENT_ROOT, CURSO_ACTUAL_ROOT, CURSO_ACTUAL_SYMLINK, DATE_FORMAT

# Tercera clase importante: Curso 
class Curso():
    def __init__(self, path):
        self.path = path
        self.name = path.stem

        self.info = yaml.safe_load((path / 'info.yaml').open()) # Abrimos la información de cada clase

        # Lazy lodeamos las Clases de cada uno de los cursos
        self._clases = None

    @property
    def clases(self):
        if not self._clases:
            self._clases = Clases(self)
        return self._clases
        
        # Cambiamos la igualdad para que sea solo si apuntan al mismo path
    def __eq__(self, other):
        if other == None:
            return False
        else:
            return self.path == other.path

# Cuarta clase importante: Cursos, hereda de list 
class Cursos(list):
    def __init__(self):
        list.__init__(self, self.read_files()) # Al iniciar crea una lista de Cursos, con base en sus paths

    def read_files(self):
        directorios_cursos = [x for x in PARENT_ROOT.iterdir() if x.is_dir() and x.name != ".git"]
        _cursos = [Curso(path) for path in directorios_cursos]
        return sorted(_cursos, key=lambda c: c.name)

    # Cursoact 
    @property # Mantiene vista la carpeta original del symlink cursoact
    def current(self):
        return Curso(CURSO_ACTUAL_ROOT.resolve())

    @current.setter
    def current(self, course):
        CURSO_ACTUAL_SYMLINK.unlink()
        CURSO_ACTUAL_SYMLINK.symlink_to(course.path)

