/* modulo_calificaciones.js  -  Módulo 5: notas de los tres parciales
   El promedio y la situación los calcula la API (reglas.py), no el navegador. */

registrarModulo({
  id: "calificaciones",
  titulo: "Calificaciones",
  grupo: "academico",
  icono: "calificaciones",
  color: "c-morado",
  descripcion: "Notas de los tres parciales, promedio y situación.",
  render: async (contenedor) => {
    const cursos = await api("/cursos");
    contenedor.innerHTML = `
      <div class="cabecera">
        <div><h2>Calificaciones</h2><p>Escriba la nota (0 a 100) de cada parcial y presione guardar. Aprueba con promedio ≥ 70.</p></div>
      </div>
      <div class="tarjeta">
        <div class="herramientas">
          <div class="buscador">${icono("buscar", 16)}<input type="search" id="cal-buscar" placeholder="Buscar estudiante…" /></div>
          <select id="cal-curso"><option value="">Todos los cursos</option>
            ${cursos.map((c) => `<option value="${c.id}">${esc(c.codigo)} · ${esc(c.nombre)}</option>`).join("")}</select>
          <select id="cal-situacion"><option value="">Todas las situaciones</option><option>Aprobado</option><option>Reprobado</option><option>En proceso</option></select>
          <span class="total" id="cal-total"></span>
        </div>
        <div id="cal-tabla"></div>
      </div>`;

    const campoNota = (n) => (f) =>
      `<input type="number" min="0" max="100" step="0.1" ${esAdmin() ? "" : "disabled"} data-nota="${n}" value="${f["parcial" + n] ?? ""}" placeholder="—" aria-label="Parcial ${n}" />`;

    const tabla = crearTabla(contenedor.querySelector("#cal-tabla"), {
      vacio: "No hay matrículas activas para calificar.",
      columnas: [
        { titulo: "Estudiante", render: (f) => `<div class="persona"><div class="avatar">${esc(iniciales(f.estudiante_nombre))}</div><strong>${esc(f.estudiante_nombre)}</strong></div>` },
        { titulo: "Curso", render: (f) => `<strong>${esc(f.curso_codigo)}</strong>` },
        { titulo: "Parcial 1", clase: "nota", render: campoNota(1) },
        { titulo: "Parcial 2", clase: "nota", render: campoNota(2) },
        { titulo: "Parcial 3", clase: "nota", render: campoNota(3) },
        { titulo: "Promedio", render: (f) => (f.promedio === null ? "—" : `<strong>${f.promedio}</strong>`) },
        { titulo: "Situación", render: (f) => insigniaEstado(f.situacion) },
      ],
      acciones: [
        {
          icono: "guardar",
          titulo: "Guardar notas",
          mostrarSi: () => esAdmin(),
          clase: "ok",
          alClick: async (fila, tr) => {
            // Leemos los tres cuadros de nota de ESA fila; vacío = todavía sin nota (null)
            const leer = (n) => {
              const valor = tr.querySelector(`[${esAdmin() ? "" : "disabled"} data-nota="${n}"]`).value.trim();
              return valor === "" ? null : Number(valor);
            };
            try {
              const guardada = await api(`/calificaciones/matricula/${fila.matricula_id}`, {
                metodo: "PUT",
                cuerpo: { parcial1: leer(1), parcial2: leer(2), parcial3: leer(3) },
              });
              Object.assign(fila, guardada); // actualiza la fila en memoria
              avisar(`Notas de ${fila.estudiante_nombre} guardadas`);
              tabla.redibujar();
            } catch (error) { avisar(error.message, "error"); }
          },
        },
      ],
    });

    async function cargar() {
      const filas = await api("/calificaciones", {
        params: {
          curso_id: contenedor.querySelector("#cal-curso").value,
          situacion: contenedor.querySelector("#cal-situacion").value,
          buscar: contenedor.querySelector("#cal-buscar").value.trim(),
        },
      });
      contenedor.querySelector("#cal-total").textContent = `${filas.length} registro${filas.length === 1 ? "" : "s"}`;
      tabla.mostrar(filas);
    }
    contenedor.querySelector("#cal-curso").onchange = cargar;
    contenedor.querySelector("#cal-situacion").onchange = cargar;
    contenedor.querySelector("#cal-buscar").addEventListener("input", conRetardo(cargar));
    await cargar();
  },
});
