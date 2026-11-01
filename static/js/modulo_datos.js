/* modulo_datos.js  -  Módulo 7: exportar/importar CSV, respaldos y datos de ejemplo */

const TABLAS_EXPORTAR = [
  ["estudiantes", "Estudiantes"], ["docentes", "Docentes"], ["cursos", "Cursos"],
  ["matriculas", "Matrículas"], ["calificaciones", "Calificaciones"],
];
const FORMATO_IMPORTAR = {
  estudiantes: "nombre, cuenta, carrera, correo, edad",
  docentes: "nombre, correo, especialidad",
  cursos: "codigo, nombre, creditos, cupo",
};

registrarModulo({
  id: "datos",
  titulo: "Datos y respaldos",
  grupo: "admin",
  icono: "datos",
  color: "c-amarillo",
  descripcion: "Exportar e importar CSV, respaldos y datos de ejemplo.",
  render: async (contenedor) => {
    contenedor.innerHTML = `
      <div class="cabecera">
        <div><h2>Datos y respaldos</h2><p>Mueva información hacia y desde Excel (CSV) y proteja la base de datos con copias de seguridad.</p></div>
      </div>

      <div class="rejilla-2 espacio">
        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Exportar a CSV</h3><small>se abre en Excel</small></div>
          <div class="tarjeta-cuerpo" style="display:flex;flex-wrap:wrap;gap:.6rem">
            ${TABLAS_EXPORTAR.map(([t, n]) => `<a class="btn btn-claro" href="/datos/exportar/${t}" download>${icono("descargar", 16)} ${n}</a>`).join("")}
          </div>
        </div>

        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Importar desde CSV</h3><small>carga masiva</small></div>
          <div class="tarjeta-cuerpo">
            <div class="formulario-linea">
              <div class="campo"><label for="imp-tabla">¿Qué desea importar?</label>
                <select id="imp-tabla">${Object.keys(FORMATO_IMPORTAR).map((t) => `<option value="${t}">${t[0].toUpperCase() + t.slice(1)}</option>`).join("")}</select></div>
              <div class="campo"><label for="imp-archivo">Archivo .csv</label><input type="file" id="imp-archivo" accept=".csv,text/csv" /></div>
            </div>
            <p class="ayuda" id="imp-formato" style="font-size:.82rem;color:var(--texto-suave);margin:.7rem 0"></p>
            <button class="btn btn-primario" id="imp-boton">${icono("subir", 16)} Importar</button>
            <div id="imp-resultado" style="margin-top:.9rem"></div>
          </div>
        </div>
      </div>

      <div class="rejilla-2">
        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Respaldos de la base de datos</h3>
            <button class="btn btn-primario btn-chico" id="resp-crear">${icono("datos", 15)} Crear respaldo</button></div>
          <div id="resp-lista"></div>
        </div>

        <div class="tarjeta">
          <div class="tarjeta-titulo"><h3>Datos de ejemplo</h3></div>
          <div class="tarjeta-cuerpo">
            <p style="margin-top:0">Carga docentes, cursos, estudiantes (ficticios), matrículas y notas para probar el sistema. Solo funciona si la base está vacía, para no mezclarlos con datos reales.</p>
            <button class="btn btn-dorado" id="demo-cargar">${icono("mas", 16)} Cargar datos de ejemplo</button>
          </div>
        </div>
      </div>`;

    // ---------- Importar
    const selectTabla = contenedor.querySelector("#imp-tabla");
    const mostrarFormato = () => {
      contenedor.querySelector("#imp-formato").innerHTML = `Primera fila = encabezados. Columnas requeridas: <code>${FORMATO_IMPORTAR[selectTabla.value]}</code>. Acepta coma o punto y coma.`;
    };
    selectTabla.onchange = mostrarFormato;
    mostrarFormato();

    contenedor.querySelector("#imp-boton").onclick = async () => {
      const archivo = contenedor.querySelector("#imp-archivo").files[0];
      if (!archivo) return avisar("Seleccione un archivo .csv", "error");
      const resultado = contenedor.querySelector("#imp-resultado");
      try {
        const contenido = await archivo.text(); // el navegador lee el archivo y lo manda como texto
        const r = await api(`/datos/importar/${selectTabla.value}`, { metodo: "POST", cuerpo: { contenido } });
        resultado.innerHTML = `
          <div class="mensaje-error" style="background:#dcfce7;color:#15803d">${r.insertados} registro(s) importado(s).${r.omitidos ? ` ${r.omitidos} omitido(s).` : ""}</div>
          ${r.errores.length ? `<table class="tabla"><thead><tr><th>Fila</th><th>Motivo</th></tr></thead><tbody>${r.errores.map((e) => `<tr><td>${e.fila}</td><td>${esc(e.motivo)}</td></tr>`).join("")}</tbody></table>` : ""}`;
        if (r.insertados) avisar(`${r.insertados} registro(s) importados`);
      } catch (error) {
        resultado.innerHTML = `<div class="mensaje-error">${esc(error.message)}</div>`;
      }
    };

    // ---------- Respaldos (el servidor los hace en un hilo; aquí esperamos a que termine)
    const lista = contenedor.querySelector("#resp-lista");
    const botonRespaldo = contenedor.querySelector("#resp-crear");
    async function cargarRespaldos() {
      const r = await api("/datos/respaldos");
      botonRespaldo.disabled = r.en_curso;
      lista.innerHTML = r.respaldos.length
        ? `<div class="tabla-contenedor"><table class="tabla"><thead><tr><th>Archivo</th><th>Tamaño</th><th>Fecha</th><th></th></tr></thead><tbody>${r.respaldos
            .slice(0, 8)
            .map((x) => `<tr><td><code>${esc(x.nombre)}</code></td><td>${x.tamano_kb} KB</td><td style="white-space:nowrap">${esc(new Date(x.fecha).toLocaleString("es-HN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }))}</td><td class="der"><a class="btn-icono" style="text-decoration:none" href="/datos/respaldos/${encodeURIComponent(x.nombre)}" title="Descargar">${icono("descargar", 16)}</a></td></tr>`)
            .join("")}</tbody></table></div>`
        : `<div class="vacio">${icono("vacio", 40)}<div>Aún no hay respaldos. Cree el primero.</div></div>`;
      return r.en_curso;
    }
    botonRespaldo.onclick = async () => {
      try {
        await api("/datos/respaldos", { metodo: "POST" });
        avisar("Respaldo iniciado en segundo plano…");
        for (let i = 0; i < 20; i++) { // preguntamos cada medio segundo si ya terminó
          await esperar(500);
          if (!(await cargarRespaldos())) break;
        }
        avisar("Respaldo terminado");
      } catch (error) { avisar(error.message, "error"); await cargarRespaldos(); }
    };
    contenedor.querySelector("#demo-cargar").onclick = async () => {
      try {
        const r = await api("/datos/demo", { metodo: "POST" });
        const c = r.creados;
        avisar(`Cargados: ${c.estudiantes} estudiantes, ${c.docentes} docentes, ${c.cursos} cursos, ${c.matriculas} matrículas`);
      } catch (error) { avisar(error.message, "error"); }
    };
    await cargarRespaldos();
  },
});
