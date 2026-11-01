/* modulo_reportes.js  -  Módulo 6: estadísticas, filtros y paginación */

function filaBarra(etiqueta, valor, maximo, textoValor, color = "") {
  const ancho = maximo ? Math.min(Math.round((100 * valor) / maximo), 100) : 0;
  return `<div class="fila-barra"><div class="etq" title="${esc(etiqueta)}">${esc(etiqueta)}</div><div class="barra ${color}"><span style="width:${ancho}%"></span></div><div class="val">${esc(textoValor)}</div></div>`;
}

registrarModulo({
  id: "reportes",
  titulo: "Reportes",
  grupo: "analisis",
  icono: "reportes",
  color: "c-rosa",
  descripcion: "Estadísticas, ocupación de cursos y listados filtrados.",
  render: async (contenedor) => {
    const [est, cursos] = await Promise.all([api("/reportes/estadisticas"), api("/cursos")]);
    const s = est.situacion;
    const evaluados = s.Aprobado + s.Reprobado + s["En proceso"];
    const pA = evaluados ? (100 * s.Aprobado) / evaluados : 0;
    const pR = evaluados ? (100 * s.Reprobado) / evaluados : 0;
    const gradiente = evaluados
      ? `conic-gradient(var(--verde) 0 ${pA}%, var(--rojo) ${pA}% ${pA + pR}%, var(--naranja) ${pA + pR}% 100%)`
      : "conic-gradient(#e2e4f0 0 100%)";
    const maxCarrera = Math.max(...est.estudiantes_por_carrera.map((c) => c.total), 1);

    contenedor.innerHTML = `
      <div class="cabecera">
        <div><h2>Reportes y estadísticas</h2><p>Explora los resultados académicos, la ocupación y la carga docente.</p></div>
        ${esAdmin() ? `<a class="btn btn-claro" href="/datos/exportar/matriculas">${icono("descargar", 16)} Exportar matrículas (CSV)</a>` : ""}
      </div>

      <div class="rejilla-2 espacio">
        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Situación académica</h3><small>Promedio general: <strong>${est.promedio_general ?? "—"}</strong></small></div>
          <div class="tarjeta-cuerpo" style="display:flex;gap:1.6rem;align-items:center;flex-wrap:wrap">
            <div class="dona" style="background:${gradiente}"><div class="dona-centro"><div>${evaluados}<small>registros</small></div></div></div>
            <div class="leyenda">
              <div><i style="background:var(--verde)"></i>Aprobados: <strong>${s.Aprobado}</strong></div>
              <div><i style="background:var(--rojo)"></i>Reprobados: <strong>${s.Reprobado}</strong></div>
              <div><i style="background:var(--naranja)"></i>En proceso: <strong>${s["En proceso"]}</strong></div>
            </div>
          </div>
        </div>

        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Mejores promedios</h3><small>Top 5 estudiantes</small></div>
          <div class="tarjeta-cuerpo">
            ${est.mejores_promedios.length
              ? est.mejores_promedios.map((m, i) => `<div class="fila-barra" style="grid-template-columns:28px 1fr 60px"><strong>${i + 1}.</strong><div class="etq">${esc(m.estudiante)} <small style="color:var(--texto-suave)">· ${m.cursos} curso${m.cursos === 1 ? "" : "s"}</small></div><div class="val">${m.promedio}</div></div>`).join("")
              : '<div class="vacio">Aún no hay promedios finales.</div>'}
          </div>
        </div>
      </div>

      <div class="rejilla-2 espacio">
        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Ocupación de cursos</h3><small>matriculados / cupo</small></div>
          <div class="tarjeta-cuerpo">
            ${est.ocupacion_cursos.length
              ? est.ocupacion_cursos.map((c) => filaBarra(`${c.codigo} · ${c.nombre}`, c.ocupacion, 100, `${c.matriculados}/${c.cupo}`, c.ocupacion >= 100 ? "rojo" : c.ocupacion >= 80 ? "naranja" : "verde")).join("")
              : '<div class="vacio">No hay cursos.</div>'}
          </div>
        </div>
        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Promedio por curso</h3><small>aprueba con 70</small></div>
          <div class="tarjeta-cuerpo">
            ${est.promedio_por_curso.length
              ? est.promedio_por_curso.map((c) => filaBarra(c.codigo, c.promedio, 100, c.promedio, c.promedio >= 70 ? "verde" : "rojo")).join("")
              : '<div class="vacio">Aún no hay notas completas.</div>'}
          </div>
        </div>
      </div>

      <div class="rejilla-2 espacio">
        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Estudiantes por carrera</h3></div>
          <div class="tarjeta-cuerpo">
            ${est.estudiantes_por_carrera.length
              ? est.estudiantes_por_carrera.map((c) => filaBarra(c.carrera, c.total, maxCarrera, c.total)).join("")
              : '<div class="vacio">No hay estudiantes.</div>'}
          </div>
        </div>
        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Carga de docentes</h3></div>
          <div id="rep-docentes"></div>
        </div>
      </div>

      <div class="tarjeta">
        <div class="tarjeta-titulo"><h3>Detalle de matrículas</h3><small>Filtra por estudiante, curso y estado</small></div>
        <div class="herramientas">
          <div class="buscador">${icono("buscar", 16)}<input type="search" id="rep-buscar" placeholder="Estudiante o cuenta…" /></div>
          <select id="rep-estado"><option value="">Todos los estados</option><option value="activa">Activas</option><option value="retirada">Retiradas</option></select>
          <select id="rep-curso"><option value="">Todos los cursos</option>${cursos.map((c) => `<option value="${c.id}">${esc(c.codigo)}</option>`).join("")}</select>
          <select id="rep-orden"><option value="fecha">Ordenar por fecha</option><option value="estudiante">Ordenar por estudiante</option><option value="curso">Ordenar por curso</option></select>
        </div>
        <div id="rep-tabla"></div>
        <div class="paginacion" id="rep-paginacion"></div>
      </div>`;

    // Tabla de carga de docentes (usa crearTabla sin acciones)
    crearTabla(contenedor.querySelector("#rep-docentes"), {
      porPagina: 6,
      vacio: "No hay docentes registrados.",
      columnas: [
        { titulo: "Docente", render: (f) => `<strong>${esc(f.nombre)}</strong><br><small style="color:var(--texto-suave)">${esc(f.especialidad)}</small>` },
        { titulo: "Cursos", clave: "cursos" },
        { titulo: "Estudiantes", clave: "estudiantes" },
      ],
    }).mostrar(est.carga_docentes);

    // Detalle paginado: aquí la paginación la hace el SERVIDOR (LIMIT/OFFSET)
    let pagina = 1;
    async function cargarDetalle() {
      const r = await api("/reportes/matriculas", {
        params: {
          pagina,
          por_pagina: 8,
          estado: contenedor.querySelector("#rep-estado").value,
          curso_id: contenedor.querySelector("#rep-curso").value,
          buscar: contenedor.querySelector("#rep-buscar").value.trim(),
          orden: contenedor.querySelector("#rep-orden").value,
          descendente: contenedor.querySelector("#rep-orden").value === "fecha",
        },
      });
      const contenedorTabla = contenedor.querySelector("#rep-tabla");
      if (!r.items.length) {
        contenedorTabla.innerHTML = `<div class="vacio">${icono("vacio", 44)}<div>No hay matrículas con esos filtros.</div></div>`;
      } else {
        contenedorTabla.innerHTML = `<div class="tabla-contenedor"><table class="tabla"><thead><tr><th>Estudiante</th><th>Carrera</th><th>Curso</th><th>Docente</th><th>Fecha</th><th>Estado</th></tr></thead><tbody>${r.items
          .map((m) => `<tr><td><strong>${esc(m.estudiante)}</strong><br><small style="color:var(--texto-suave)">${esc(m.cuenta)}</small></td><td>${esc(m.carrera)}</td><td>${esc(m.curso_codigo)}</td><td>${esc(m.docente || "—")}</td><td>${esc(formatearFecha(m.fecha_matricula))}</td><td>${insigniaEstado(m.estado)}</td></tr>`)
          .join("")}</tbody></table></div>`;
      }
      const pie = contenedor.querySelector("#rep-paginacion");
      pie.innerHTML = `<span>${r.total} resultado${r.total === 1 ? "" : "s"} · página ${r.pagina} de ${r.paginas}</span>
        <div class="botones"><button id="rep-ant" ${r.pagina <= 1 ? "disabled" : ""}>‹</button><button id="rep-sig" ${r.pagina >= r.paginas ? "disabled" : ""}>›</button></div>`;
      pie.querySelector("#rep-ant").onclick = () => { pagina--; cargarDetalle(); };
      pie.querySelector("#rep-sig").onclick = () => { pagina++; cargarDetalle(); };
    }
    ["#rep-estado", "#rep-curso", "#rep-orden"].forEach((id) => (contenedor.querySelector(id).onchange = () => { pagina = 1; cargarDetalle(); }));
    contenedor.querySelector("#rep-buscar").addEventListener("input", conRetardo(() => { pagina = 1; cargarDetalle(); }));
    await cargarDetalle();
  },
});
