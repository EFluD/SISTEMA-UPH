/* Fichas académicas: cada vista consume un endpoint de lectura protegido. */
function tablaConsulta(columnas, filas) {
  if (!filas.length) return '<div class="vacio">No hay registros para esta selección.</div>';
  return `<div class="tabla-contenedor"><table class="tabla"><thead><tr>${columnas.map(c=>`<th>${esc(c[0])}</th>`).join("")}</tr></thead><tbody>${filas.map(f=>`<tr>${columnas.map(c=>`<td>${esc(f[c[1]] ?? "—")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
function accionesConsulta(contenedor, filas, titulo, alClick) {
  contenedor.querySelectorAll("tbody tr").forEach((tr,i)=> {
    const celda=document.createElement("td"), boton=document.createElement("button");
    boton.className="btn btn-claro btn-chico"; boton.textContent=titulo;
    boton.onclick=()=>alClick(filas[i]); celda.appendChild(boton); tr.appendChild(celda);
  });
  const encabezado=contenedor.querySelector("thead tr");
  if(encabezado) {const th=document.createElement("th"); th.textContent="Detalle"; encabezado.appendChild(th);}
}
function opcionesPeriodo(periodos, valor="") {
  return `<option value="">Todos los períodos</option>${periodos.map(p=>`<option value="${esc(p)}" ${p===valor?"selected":""}>${esc(p)}</option>`).join("")}`;
}
function imprimirConsulta(elemento) {
  const fondo=elemento.closest(".fondo-modal");
  fondo.classList.add("para-imprimir"); document.body.classList.add("imprimiendo");
  window.print();
  fondo.classList.remove("para-imprimir"); document.body.classList.remove("imprimiendo");
}
async function verExpediente(id, periodoInicial) {
  try {
    const periodos=await api("/academico/periodos");
    const periodo=periodoInicial === undefined ? periodos.find(p=>p!=="Sin período") || periodos[0] || "" : periodoInicial;
    const ventana=abrirModal({titulo:"Expediente académico", grande:true,
      cuerpo:`<div class="expediente-cabecera"></div><div class="expediente-herramientas"><div class="pestanas" role="group" aria-label="Vista del expediente"><button class="actual" data-vista="hoja" aria-pressed="true">Hoja de matrícula</button><button data-vista="historial" aria-pressed="false">Historial completo</button></div><label>Período de la hoja<select id="exp-periodo">${opcionesPeriodo(periodos,periodo)}</select></label><button class="btn btn-claro" data-imprimir>Imprimir / PDF</button></div><div class="expediente-datos" aria-live="polite">Cargando…</div>`});
    let vista="hoja", revision=0;
    const elemento=ventana.elemento, datos=elemento.querySelector(".expediente-datos");
    const seleccionar=elemento.querySelector("#exp-periodo");
    if(periodo) seleccionar.value=periodo;
    elemento.querySelector("[data-imprimir]").onclick=()=>imprimirConsulta(elemento);
    async function cargar() {
      const actual=++revision;
      try {
        const r=await api(`/academico/estudiantes/${id}`,{params:{periodo:seleccionar.value}});
        if(actual!==revision || !elemento.isConnected) return;
        const e=r.estudiante;
        elemento.querySelector(".expediente-cabecera").innerHTML=`<div class="avatar avatar-grande">${esc(iniciales(e.nombre))}</div><div><span class="sobrelinea">EXPEDIENTE DEL ESTUDIANTE</span><h2>${esc(e.nombre)}</h2><p>${esc(e.cuenta)} · ${esc(e.carrera)}</p><small>${esc(e.correo)}</small></div>`;
        const seleccion=seleccionar.value || "Todos los períodos";
        const resumen= vista==="hoja" ? `<div class="resumen-exp"><div><strong>${r.resumen.clases_inscritas}</strong><span>Clases inscritas</span></div><div><strong>${r.resumen.creditos_inscritos}</strong><span>UV inscritas</span></div><div><strong>${r.resumen.clases_en_proceso}</strong><span>Clases sin nota final</span></div></div>` : `<p class="nota-consulta">${r.historial.length} registros de matrícula · ${r.resumen.creditos_aprobados} UV aprobadas según registros vigentes. Incluye retiros.</p>`;
        const columnas= vista==="hoja" ? [["Código","codigo"],["Curso","curso"],["Período","periodo"],["UV","creditos"],["Docente","docente"],["Horario","horario"],["Aula","aula"]] : [["Período","periodo"],["Código","codigo"],["Curso","curso"],["UV","creditos"],["P1","parcial1"],["P2","parcial2"],["P3","parcial3"],["Promedio","promedio"],["Resultado","situacion"],["Matrícula","estado"]];
        datos.innerHTML=`<h3>${vista==="hoja" ? "Hoja de matrícula · "+esc(seleccion) : "Historial académico · todos los períodos"}</h3>${resumen}${tablaConsulta(columnas, vista==="hoja" ? r.hoja : r.historial)}<p class="nota-consulta">${vista==="hoja" ? "Las matrículas retiradas no suman clases ni UV inscritas. " : "La nota de aprobación es 70. "}Documento de consulta académica, sin validación institucional.</p>`;
      } catch(e) {if(actual===revision) datos.textContent=e.message;}
    }
    seleccionar.onchange=cargar;
    elemento.querySelectorAll("[data-vista]").forEach(b=>b.onclick=()=> {vista=b.dataset.vista; elemento.querySelectorAll("[data-vista]").forEach(t=>{t.classList.toggle("actual",t===b);t.setAttribute("aria-pressed",String(t===b));}); seleccionar.disabled=vista==="historial"; cargar();});
    await cargar();
  } catch(e) {avisar(e.message,"error");}
}
async function verCargaDocente(id, periodoInicial="") {
  try {
    const periodos=await api("/academico/periodos");
    const ventana=abrirModal({titulo:"Carga académica docente",grande:true,cuerpo:`<div class="expediente-herramientas"><label>Período<select id="doc-periodo">${opcionesPeriodo(periodos,periodoInicial)}</select></label></div><div id="doc-carga" aria-live="polite">Cargando…</div>`});
    const elemento=ventana.elemento, contenido=elemento.querySelector("#doc-carga"); let revision=0;
    async function cargar() {
      const actual=++revision;
      try {
        const r=await api(`/academico/docentes/${id}`,{params:{periodo:elemento.querySelector("#doc-periodo").value}});
        if(actual!==revision || !elemento.isConnected) return;
        contenido.innerHTML=`<div class="expediente-cabecera"><div class="avatar avatar-grande">${esc(iniciales(r.docente.nombre))}</div><div><span class="sobrelinea">CARGA DOCENTE</span><h2>${esc(r.docente.nombre)}</h2><p>${esc(r.docente.especialidad)}</p></div></div><div class="resumen-exp"><div><strong>${r.total_cursos}</strong><span>Cursos asignados</span></div><div><strong>${r.total_inscripciones}</strong><span>Inscripciones en sus cursos</span></div></div>${tablaConsulta([["Código","codigo"],["Curso","nombre"],["Período","periodo"],["Horario","horario"],["Aula","aula"],["Inscritos","matriculados"]],r.cursos)}<p class="nota-consulta">Las inscripciones suman matrículas; un alumno puede estar en varios cursos.</p>`;
        accionesConsulta(contenido,r.cursos,"Ver alumnos",c=>verListaCurso(c.id));
      } catch(e) {if(actual===revision) contenido.textContent=e.message;}
    }
    elemento.querySelector("#doc-periodo").onchange=cargar; await cargar();
  } catch(e) {avisar(e.message,"error");}
}
async function verListaCurso(id) {
  try {
    const r=await api(`/academico/cursos/${id}`);
    const c=r.curso;
    const ventana=abrirModal({titulo:`${c.codigo} · ${c.nombre}`,grande:true,cuerpo:`<p class="nota-consulta">${esc(c.periodo)} · ${esc(c.docente || "Sin docente")} · ${r.estudiantes.length} estudiantes inscritos</p>${tablaConsulta([["Cuenta","cuenta"],["Estudiante","estudiante"],["Carrera","carrera"],["Promedio","promedio"],["Situación","situacion"]],r.estudiantes)}`});
    accionesConsulta(ventana.elemento,r.estudiantes,"Ver expediente",e=>verExpediente(e.estudiante_id,c.periodo));
  } catch(e) {avisar(e.message,"error");}
}
