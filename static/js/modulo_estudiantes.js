/* modulo_estudiantes.js  -  Módulo 1: Estudiantes
   Solo describe QUÉ columnas y campos tiene; renderCrud() (nucleo.js) hace el resto. */

const CARRERAS = [
  "Ingeniería en Sistemas Computacionales",
  "Ingeniería Industrial",
  "Administración de Empresas",
  "Ingeniería Civil",
];

registrarModulo({
  id: "estudiantes",
  titulo: "Estudiantes",
  grupo: "academico",
  icono: "estudiantes",
  color: "c-verde",
  descripcion: "Registro de estudiantes: cuenta, carrera y correo.",
  render: (contenedor) =>
    renderCrud(contenedor, {
      titulo: "Estudiantes",
      descripcion: "Registre, busque y actualice a los estudiantes.",
      singular: "estudiante",
      plural: "estudiantes",
      articulo: "al",
      ruta: "/estudiantes",
      nombreFila: (f) => f.nombre,
      columnas: [
        { titulo: "Cuenta", clave: "cuenta" },
        {
          titulo: "Estudiante",
          render: (f) => `<div class="persona"><div class="avatar">${esc(iniciales(f.nombre))}</div><div><strong>${esc(f.nombre)}</strong><small>${esc(f.correo)}</small></div></div>`,
        },
        { titulo: "Carrera", clave: "carrera" },
        { titulo: "Edad", clave: "edad" },
      ],
      campos: [
        { clave: "nombre", etiqueta: "Nombre completo", requerido: true, minlength: 3, ancho: true },
        { clave: "cuenta", etiqueta: "Número de cuenta", requerido: true },
        { clave: "edad", etiqueta: "Edad", tipo: "number", min: 15, max: 100, requerido: true },
        { clave: "carrera", etiqueta: "Carrera", requerido: true, sugerencias: CARRERAS, ancho: true },
        { clave: "correo", etiqueta: "Correo electrónico", tipo: "email", requerido: true, ancho: true },
      ],
      // Acción extra: ver los cursos de este estudiante (endpoint del reto de la Semana 2)
      acciones: [
        {
          icono: "ver",
          titulo: "Matrícula e historial",
          alClick: (fila) => verExpediente(fila.id),
        },
      ],
    }),
});
