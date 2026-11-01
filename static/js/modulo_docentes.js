/* modulo_docentes.js  -  Módulo 2: Docentes */

registrarModulo({
  id: "docentes",
  titulo: "Docentes",
  grupo: "academico",
  icono: "docentes",
  color: "c-naranja",
  descripcion: "Docentes, su especialidad y los cursos que imparten.",
  render: (contenedor) =>
    renderCrud(contenedor, {
      titulo: "Docentes",
      descripcion: "Cada docente puede tener varios cursos asignados.",
      singular: "docente",
      plural: "docentes",
      articulo: "al",
      ruta: "/docentes",
      nombreFila: (f) => f.nombre,
      columnas: [
        {
          titulo: "Docente",
          render: (f) => `<div class="persona"><div class="avatar">${esc(iniciales(f.nombre))}</div><div><strong>${esc(f.nombre)}</strong><small>${esc(f.correo)}</small></div></div>`,
        },
        { titulo: "Especialidad", clave: "especialidad" },
        { titulo: "Cursos asignados", render: (f) => insignia(f.total_cursos === 1 ? "1 curso" : `${f.total_cursos} cursos`, f.total_cursos ? "azul" : "gris") },
      ],
      campos: [
        { clave: "nombre", etiqueta: "Nombre completo", requerido: true, ancho: true },
        { clave: "correo", etiqueta: "Correo electrónico", tipo: "email", requerido: true },
        { clave: "especialidad", etiqueta: "Especialidad", requerido: true },
      ],
      acciones: [
        {
          icono: "cursos",
          titulo: "Ver sus cursos",
          alClick: (fila) => verCargaDocente(fila.id),
        },
      ],
    }),
});
