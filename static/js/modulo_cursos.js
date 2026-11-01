/* modulo_cursos.js  -  Módulo 3: Cursos (cada curso puede tener un docente) */

registrarModulo({
  id: "cursos",
  titulo: "Cursos",
  grupo: "academico",
  icono: "cursos",
  color: "c-cian",
  descripcion: "Oferta de cursos con créditos, cupo y docente asignado.",
  render: (contenedor) =>
    renderCrud(contenedor, {
      titulo: "Cursos",
      descripcion: "Defina los cursos, su cupo y el docente que los imparte.",
      singular: "curso",
      plural: "cursos",
      articulo: "el",
      ruta: "/cursos",
      nombreFila: (f) => `${f.codigo} · ${f.nombre}`,
      columnas: [
        { titulo: "Código", render: (f) => `<strong>${esc(f.codigo)}</strong>` },
        { titulo: "Curso", clave: "nombre" },
        { titulo: "UV", clave: "creditos" },
        { titulo: "Período", clave: "periodo" },
        { titulo: "Docente", render: (f) => (f.docente_nombre ? esc(f.docente_nombre) : insignia("Sin asignar", "gris")) },
        {
          titulo: "Ocupación",
          render: (f) => {
            const porcentaje = Math.min(Math.round((100 * f.matriculados) / f.cupo), 100);
            const color = porcentaje >= 100 ? "rojo" : porcentaje >= 80 ? "naranja" : "verde";
            return `<div style="min-width:130px"><div style="font-size:.8rem;margin-bottom:3px">${f.matriculados} / ${f.cupo} cupos</div><div class="barra ${color}"><span style="width:${porcentaje}%"></span></div></div>`;
          },
        },
      ],
      campos: [
        {clave:"periodo", etiqueta:"Período académico", requerido:true, placeholder:"2026-3"},
        {clave:"horario", etiqueta:"Horario (informativo)", placeholder:"LU-MI · 07:00–09:00"},
        {clave:"aula", etiqueta:"Aula", placeholder:"LAB-01"},
        { clave: "codigo", etiqueta: "Código", requerido: true, placeholder: "IS-151" },
        { clave: "creditos", etiqueta: "Unidades valorativas", tipo: "number", min: 1, max: 10, requerido: true },
        { clave: "nombre", etiqueta: "Nombre del curso", requerido: true, ancho: true },
        { clave: "cupo", etiqueta: "Cupo máximo", tipo: "number", min: 1, max: 500, requerido: true },
        {
          clave: "docente_id",
          etiqueta: "Docente",
          tipo: "select",
          opcional: true,
          numero: true,
          opciones: async () => [
            { valor: "", etiqueta: "— Sin docente —" },
            ...(await api("/docentes")).map((d) => ({ valor: d.id, etiqueta: d.nombre })),
          ],
        },
      ],
    }),
});
