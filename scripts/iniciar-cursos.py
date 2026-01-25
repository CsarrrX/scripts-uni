from cursos import Cursos

for curso in Cursos():
        clases = curso.clases
        curso = clases.curso.info["title"]
        lineas = [r'\documentclass[a4paper]{report}',
                 r'\input{../preamble.tex}',
                 fr'\title{{{curso}}}',
                 r'\begin{document}',
                 r'    \maketitle',
                 r'    \tableofcontents',
                 fr'    % inicio clases',
                 fr'    % fin clases',
                 r'\end{document}'
                ]
        clases.master_file.touch()
        clases.master_file.write_text('\n'.join(lineas))
        (clases.root / 'master.tex.latexmain').touch()
        (clases.root / 'figures').mkdir(exist_ok=True)
