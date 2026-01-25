import subprocess
from cursos import Cursos
import compilar_todo 


def wofi_menu(opciones, prompt='Selecciona notas'):
    #Ejecutamos wofi: 
    proceso = subprocess.Popen(
        ['wofi', '--dmenu', '-p', prompt],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    seleccion, _ = proceso.communicate(input="\n".join(opciones))
    return seleccion.strip()

def main():
    cursos = Cursos()
    nombres_cursos = [c.name for c in cursos]

    curso_nombre = wofi_menu(nombres_cursos, 'Selecciona un curso:')
    if not curso_nombre:
        return -1 
    
    curso = next(c for c in cursos if c.name == curso_nombre)
    clases = curso.clases

    acciones = ['Nueva nota', 'Compilar master', 'Editar una nota', 'Compilar todo (drive)']
    accion = wofi_menu(acciones, f"Selecciona acción para el curso {curso_nombre}:")

    if accion == 'Nueva nota':
        nueva = curso.clases.nueva_clase()
        nueva.editar()
        if nueva.number != 1:
            r = clases.parser_clase_range("previa-ultima")
            clases.update_clases_master(r)
        else:
            r = clases.parser_clase_range(1)
        clases.compile_master()

    elif accion == 'Compilar master':
        try:
            rango_str = subprocess.check_output(
            ["wofi", "--dmenu", "--print-query", "--prompt", "Rango (ej: previa-ultima):"],
            text=True
            ).strip().split('\n')[-1]
            
            if rango_str: 
                r = clases.parser_clase_range(rango_str)
                clases.update_clases_master(r)
                clases.compile_master()
        except subprocess.CalledProcessError:
            pass # Si presionas ESC en wofi

    elif accion == 'Editar una nota':
        notas = [n.file_path.stem for n in clases]
        nota_stem = wofi_menu(notas, 'Selecciona una nota:')
        if nota_stem:
            nota = next(n for n in clases if n.stem == nota_stem)
            nota.editar()
            r = clases.parser_clase_range(nota.number)
            clases.update_clases_master(r)
            clases.compile_master()

    elif accion == 'Compilar todo (drive)': 
        compilar_todo.main()

if __name__ == "__main__":
    main()
