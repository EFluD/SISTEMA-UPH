/* modulo_matriculas.js  -  Módulo 4: Matrículas (reglas: existe, cupo, no repetido) */

registrarModulo({
  id: "matriculas",
  titulo: "Matrículas",
  grupo: "academico",
  icono: "matriculas",
  color: "c-azul",
  descripcion: "Matricule estudiantes en cursos y controle los retiros.",
  render: async (contenedor) => {
    const [estudiantes, cursos] = await Promise.all([api("/estudiantes"), api("/cursos")]);

    contenedor.innerHTML = `
      <div class="cabecera">
        <div><h2>Matrículas</h2><p>Gestiona las inscripciones y conserva el registro de los retiros.</p></div>
      </div>

      <div class="tarjeta espacio">
        <div class="tarjeta-titulo"><h3>Nueva matrícula</h3></div>
        <div class="tarjeta-cuerpo">
          <div class="formulario-linea">
            <div class="campo"><label for="mat-estudiante">Estudiante</label>
              <select id="mat-estudiante"><option value="">Seleccione un estudiante</option>
                ${estudiantes.map((e) => `<option value="${e.id}">${esc(e.nombre)} (${esc(e.cuenta)})</option>`).join("")}
              </select></div>
            <div class="campo"><label for="mat-curso">Curso</label>
              <select id="mat-curso"><option value="">Seleccione un curso</option>
                ${cursos.map((c) => `<option value="${c.id}">${esc(c.codigo)} · ${esc(c.nombre)} (${c.cupo - c.matriculados} cupos)</option>`).join("")}
              </select></div>
            <button class="btn btn-primario" id="mat-crear">${icono("mas", 16)} Matricular</button>
          </div>
        </div>
      </div>

      <div class="tarjeta">
        <div class="herramientas">
          <div class="buscador">${icono("buscar", 16)}<input type="search" id="mat-buscar" placeholder="Buscar por estudiante o curso…" /></div>
          <select id="mat-estado"><option value="">Todos los estados</option><option value="activa">Activas</option><option value="retirada">Retiradas</option></select>
          <select id="mat-filtro-curso"><option value="">Todos los cursos</option>
            ${cursos.map((c) => `<option value="${c.id}">${esc(c.codigo)}</option>`).join("")}</select>
          <span class="total" id="mat-total"></span>
        </div>
        <div id="mat-tabla"></div>
      </div>`;

    contenedor.querySelector("#mat-crear").closest(".tarjeta").hidden = !esAdmin();
    const tabla = crearTabla(contenedor.querySelector("#mat-tabla"), {
      vacio: "No hay matrículas con esos filtros.",
      columnas: [
        { titulo: "#", clave: "id" },
        { titulo: "Estudiante", render: (f) => `<div class="persona"><div class="avatar">${esc(iniciales(f.estudiante_nombre))}</div><strong>${esc(f.estudiante_nombre)}</strong></div>` },
        { titulo: "Curso", render: (f) => `<strong>${esc(f.curso_codigo)}</strong> <small style="color:var(--texto-suave)">${esc(f.curso_nombre)}</small>` },
        { titulo: "Fecha", render: (f) => esc(formatearFecha(f.fecha_matricula)) },
        { titulo: "Estado", render: (f) => insigniaEstado(f.estado) },
      ],
      acciones: [
        {
          icono: "cerrar",
          titulo: "Retirar matrícula",
          clase: "peligro",
          mostrarSi: (f) => esAdmin() && f.estado === "activa",
          alClick: async (fila) => {
            if (!(await confirmar(`¿Retirar a ${fila.estudiante_nombre} de ${fila.curso_codigo}? Quedará en el historial como "retirada".`, "Retirar"))) return;
            try {
              await api(`/matriculas/${fila.id}`, { metodo: "DELETE" });
              avisar("Matrícula retirada");
              await cargar({ conservarPagina: true });
            } catch (error) { avisar(error.message, "error"); }
          },
        },
      ],
    });

    let todas = [];
    function filtrarEnPantalla({ conservarPagina = false } = {}) {
      const texto = contenedor.querySelector("#mat-buscar").value.trim().toLowerCase();
      const filas = todas.filter((m) => !texto || `${m.estudiante_nombre} ${m.curso_nombre} ${m.curso_codigo}`.toLowerCase().includes(texto));
      contenedor.querySelector("#mat-total").textContent = `${filas.length} matrícula${filas.length === 1 ? "" : "s"}`;
      tabla.mostrar(filas, { conservarPagina });
    }
    async function cargar(opciones = {}) {
      todas = await api("/matriculas", {
        params: { estado: contenedor.querySelector("#mat-estado").value, curso_id: contenedor.querySelector("#mat-filtro-curso").value },
      });
      todas.reverse(); // las más nuevas primero
      filtrarEnPantalla(opciones);
    }

    contenedor.querySelector("#mat-buscar").addEventListener("input", () => filtrarEnPantalla());
    contenedor.querySelector("#mat-estado").onchange = () => cargar();
    contenedor.querySelector("#mat-filtro-curso").onchange = () => cargar();
    contenedor.querySelector("#mat-crear").onclick = async () => {
      const estudiante_id = Number(contenedor.querySelector("#mat-estudiante").value);
      const curso_id = Number(contenedor.querySelector("#mat-curso").value);
      if (!estudiante_id || !curso_id) return avisar("Seleccione un estudiante y un curso", "error");
      try {
        await api("/matriculas", { metodo: "POST", cuerpo: { estudiante_id, curso_id } });
        avisar("Matrícula registrada");
        await cargar();
      } catch (error) { avisar(error.message, "error"); } // 404, 409 (sin cupo / repetida)
    };
    await cargar();
  },
});
