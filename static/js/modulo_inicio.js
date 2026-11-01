/* Panel interactivo: un filtro común y detalles que explican cada indicador. */
registrarModulo({
  id:"inicio", titulo:"Inicio", grupo:"principal", icono:"inicio", color:"c-azul", descripcion:"Una mirada al campus.",
  render:async contenedor => {
    const periodos=await api("/academico/periodos");
    contenedor.innerHTML=`
      <section class="bienvenida">
        <div><span class="sobrelinea">PANORAMA ACADÉMICO</span><h1>Una mirada a tu campus<span>.</span></h1><p>Hola, ${esc(window.USUARIO.nombre)}. Aquí comienza el seguimiento de tu comunidad académica.</p></div>
        <div class="filtro-campus"><label for="panel-periodo">Período académico</label><select id="panel-periodo">${opcionesPeriodo(periodos)}</select></div>
      </section>
      <div class="banda-contexto"><span class="punto-verde"></span><span id="panel-contexto">Preparando resumen…</span><button class="enlace-boton" id="panel-actualizar">Actualizar datos ${icono("flecha",14)}</button></div>
      <section class="metricas-campus" id="panel-metricas" aria-label="Indicadores interactivos"></section>
      <div class="panorama-rejilla">
        <section class="tarjeta"><div class="tarjeta-titulo"><div><span class="sobrelinea">OFERTA ACADÉMICA</span><h3>Cursos y ocupación</h3></div><a href="#/cursos" class="enlace-sutil">Ver cursos ${icono("flecha",15)}</a></div><div id="panel-cursos" class="tarjeta-cuerpo"></div></section>
        <section class="tarjeta"><div class="tarjeta-titulo"><div><span class="sobrelinea">SEGUIMIENTO</span><h3>Situación académica</h3></div></div><div id="panel-situacion" class="tarjeta-cuerpo"></div></section>
      </div>
      <div class="panorama-rejilla inferior">
        <section class="tarjeta"><div class="tarjeta-titulo"><div><span class="sobrelinea">EQUIPO ACADÉMICO</span><h3>Carga de docentes</h3></div><a href="#/docentes" class="enlace-sutil">Ver todos</a></div><div id="panel-docentes"></div></section>
        <section class="tarjeta"><div class="tarjeta-titulo"><div><span class="sobrelinea">ACTIVIDAD RECIENTE</span><h3>Últimas matrículas activas</h3></div><a href="#/matriculas" class="enlace-sutil">Ver todas</a></div><div id="panel-recientes"></div></section>
      </div>
      <p class="pie-campus">GESTIÓN ACADÉMICA · PROGRAMACIÓN III <span>Información conectada, decisiones claras.</span></p>`;
    let revision=0, r=null;
    const selector=contenedor.querySelector("#panel-periodo");
    const cuadro=(titulo,columnas,filas,accion)=> {
      const v=abrirModal({titulo,grande:true,cuerpo:tablaConsulta(columnas,filas)});
      if(accion) accionesConsulta(v.elemento,filas,"Ver detalle",accion);
    };
    const verMatriculas=filas=>cuadro("Detalle de matrículas",[["Cuenta","cuenta"],["Estudiante","estudiante"],["Curso","curso"],["Período","periodo"],["Promedio","promedio"],["Situación","situacion"]],filas,e=>verExpediente(e.estudiante_id,selector.value));
    async function cargar() {
      const actual=++revision;
      contenedor.querySelector("#panel-contexto").textContent="Actualizando resumen…";
      try {
        const datos=await api("/academico/resumen",{params:{periodo:selector.value}});
        if(actual!==revision || !contenedor.isConnected) return;
        r=datos;
        contenedor.querySelector("#panel-contexto").textContent=selector.value ? `Datos del período ${selector.value} · estudiantes con matrícula activa y docentes asignados` : "Vista general · todos los períodos y todas las personas registradas";
        const tarjetas=[["estudiantes","Estudiantes","Comunidad estudiantil","c-verde"],["docentes","Docentes","Equipo académico","c-naranja"],["cursos","Cursos","Oferta registrada","c-azul"],["matriculas","Matrículas activas","Inscripciones vigentes","c-cian"]];
        contenedor.querySelector("#panel-metricas").innerHTML=tarjetas.map(([clave,nombre,sub,color])=>`<button class="metrica-campus" data-metrica="${clave}"><div class="metrica-cab"><span>${nombre}</span><i class="${color}">${icono(clave,19)}</i></div><strong>${r.totales[clave]}</strong><div class="metrica-pie"><span>${sub}</span>${icono("flecha",16)}</div></button>`).join("");
        contenedor.querySelectorAll("[data-metrica]").forEach(b=>b.onclick=()=>{
          const k=b.dataset.metrica;
          if(k==="estudiantes") cuadro("Estudiantes",[["Cuenta","cuenta"],["Nombre","nombre"],["Carrera","carrera"]],r.estudiantes,e=>verExpediente(e.id,selector.value));
          if(k==="docentes") cuadro("Carga de docentes",[["Docente","nombre"],["Cursos","cursos"],["Inscripciones","inscripciones"]],r.docentes,d=>verCargaDocente(d.id,selector.value));
          if(k==="cursos") cuadro("Cursos del período",[["Código","codigo"],["Curso","nombre"],["Período","periodo"],["Docente","docente"],["Inscritos","matriculados"],["Cupo","cupo"]],r.cursos,c=>verListaCurso(c.id));
          if(k==="matriculas") verMatriculas(r.matriculas);
        });
        const top=[...r.cursos].sort((a,b)=>b.matriculados-a.matriculados).slice(0,5);
        contenedor.querySelector("#panel-cursos").innerHTML=top.length ? top.map(c=>`<button class="curso-ocupacion" data-curso="${c.id}"><div><span class="curso-codigo">${esc(c.codigo)}</span><strong>${esc(c.nombre)}</strong><span class="curso-cupo">${c.matriculados}<small> / ${c.cupo}</small></span></div><progress max="${c.cupo}" value="${c.matriculados}" aria-label="Ocupación de ${esc(c.nombre)}"></progress></button>`).join("")+`<div class="capacidad-campus"><span>Capacidad disponible</span><strong>${r.cupos-r.ocupados} de ${r.cupos} cupos</strong></div>` : '<div class="vacio">Sin cursos registrados. El administrador puede cargar datos de ejemplo desde Datos y respaldos.</div>';
        contenedor.querySelectorAll("[data-curso]").forEach(b=>b.onclick=()=>verListaCurso(Number(b.dataset.curso)));
        const total=r.matriculas.length, a=r.situacion.Aprobado, re=r.situacion.Reprobado;
        const pa=total?100*a/total:0, pr=total?100*re/total:0;
        contenedor.querySelector("#panel-situacion").innerHTML=`<div class="anillo-situacion"><div class="anillo" style="background:conic-gradient(var(--verde) 0 ${pa}%,var(--rojo) ${pa}% ${pa+pr}%,${total?"var(--dorado)":"var(--borde)"} ${pa+pr}% 100%)"><div><strong>${total}</strong><span>matrículas</span></div></div></div><div class="leyenda-campus">${[["Aprobado","Aprobadas","verde"],["Reprobado","Reprobadas","rojo"],["En proceso","Sin nota final","dorado"]].map(([k,n,c])=>`<button data-situacion="${k}"><i class="punto-${c}"></i><span>${n}</span><strong>${r.situacion[k]}</strong>${icono("flecha",13)}</button>`).join("")}</div><p class="nota-consulta">Selecciona un resultado para ver sus matrículas. Aprobación: 70 o más.</p>`;
        contenedor.querySelectorAll("[data-situacion]").forEach(b=>b.onclick=()=>verMatriculas(r.matriculas.filter(m=>m.situacion===b.dataset.situacion)));
        const docentes=[...r.docentes].sort((a,b)=>b.cursos-a.cursos).slice(0,5);
        const dc=contenedor.querySelector("#panel-docentes");
        dc.innerHTML=tablaConsulta([["Docente","nombre"],["Cursos","cursos"],["Inscripciones","inscripciones"]],docentes);
        accionesConsulta(dc,docentes,"Ver carga",d=>verCargaDocente(d.id,selector.value));
        const recientes=r.matriculas.slice(0,5), mc=contenedor.querySelector("#panel-recientes");
        mc.innerHTML=tablaConsulta([["Estudiante","estudiante"],["Curso","codigo"],["Período","periodo"]],recientes);
        accionesConsulta(mc,recientes,"Ver ficha",e=>verExpediente(e.estudiante_id,selector.value));
      } catch(e) {if(actual===revision) contenedor.querySelector("#panel-contexto").textContent=e.message;}
    }
    selector.onchange=cargar;
    contenedor.querySelector("#panel-actualizar").onclick=cargar;
    await cargar();
  }
});
