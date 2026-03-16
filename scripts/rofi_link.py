import subprocess
from cursos import Cursos
import compilar_todo 
from generar_formulario import generar_formulario

def rofi_menu(opciones, prompt='Selecciona notas'):
    proceso = subprocess.Popen(
        ['rofi', '-dmenu', '-p', prompt, '-i'], 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    seleccion, _ = proceso.communicate(input="\n".join(opciones))
    return seleccion.strip()

def main():
    cursos = Cursos()
    nombres_cursos = [c.name for c in cursos if c.name != "cursoact"] + ["Compilar todo (drive)", "Crear nota en cursoact"]

    curso_nombre = rofi_menu(nombres_cursos, 'Selecciona un curso:')
    if not curso_nombre:
        return -1 

    if curso_nombre == "Compilar todo (drive)":
        compilar_todo.main()
        return -1

    if curso_nombre == "Crear nota en cursoact":
        cursoact = next(c for c in cursos if c.name == "cursoact")
        nueva = cursoact.clases.nueva_clase()
        nueva.editar()
        return -1

    curso = next(c for c in cursos if c.name == curso_nombre)
    clases = curso.clases

    acciones = ['Nueva nota', 'Compilar master', 'Editar una nota', 'Generar formulario']
    accion = rofi_menu(acciones, f"Acción para {curso_nombre}:")

    if accion == 'Nueva nota':
        nueva = curso.clases.nueva_clase()
        nueva.editar()

        r = clases.parser_clase_range("todas")
        clases.update_clases_master(r)
        clases.compile_master()

    elif accion == 'Compilar master':
        opciones_master = ['todas', 'ultima', 'previa-ultima']
        rango_str = rofi_menu(opciones_master, "Rango (ej: previa-ultima):")
        
        if rango_str: 
            r = clases.parser_clase_range(rango_str)
            clases.update_clases_master(r)
            clases.compile_master()

    elif accion == 'Editar una nota':
        notas = [n.file_path.stem for n in clases]
        nota_stem = rofi_menu(notas, 'Selecciona una nota:')
        if nota_stem:
            nota = next(n for n in clases if n.file_path.stem == nota_stem)
            nota.editar()
            if nota.number != 1:
                r = clases.parser_clase_range("todas")
                clases.update_clases_master(r)
            else:
                r =  clases.parser_clase_range("1")
            clases.compile_master()

    elif accion == 'Generar formulario':
        generar_formulario(curso)

if __name__ == "__main__":
    main()
