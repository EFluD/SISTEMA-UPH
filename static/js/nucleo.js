/* =====================================================================
   nucleo.js  -  Funciones compartidas por TODOS los módulos del panel
   ---------------------------------------------------------------------
   Aquí no hay nada de estudiantes ni cursos. Solo herramientas:
     api()            -> llama a la API (fetch) y maneja los errores
     avisar()         -> mensajitos de "Guardado correctamente"
     abrirFormulario()-> ventana con un formulario (crear/editar)
     confirmar()      -> ventana de "¿Está seguro?"
     crearTabla()     -> tabla con paginación
     registrarModulo()-> agrega un módulo al menú
     iniciarAplicacion() -> arranca el menú y el router
   ===================================================================== */
"use strict";
window.USUARIO = {nombre:document.body.dataset.usuario, rol:document.body.dataset.rol};
const esAdmin = () => window.USUARIO.rol === "admin";
const cookieCSRF = () => decodeURIComponent((document.cookie.split("; ").find(c=>c.startsWith("csrf=")) || "csrf=").slice(5));

// ------------------------------------------------------------------ Íconos
// Íconos SVG dibujados con líneas (estilo "feather"). Sin librerías externas,
// así el sistema funciona aunque no haya internet en el laboratorio.
const ICONOS = {
  inicio: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  estudiantes: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  docentes: '<path d="M22 10L12 5 2 10l10 5 10-5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>',
  cursos: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  matriculas: '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M9 14l2 2 4-4"/>',
  calificaciones: '<circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>',
  reportes: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
  datos: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
  usuarios: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
  menu: '<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>',
  salir: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
  buscar: '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
  editar: '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>',
  borrar: '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>',
  mas: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  cerrar: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  guardar: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
  descargar: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
  subir: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
  ok: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
  alerta: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
  flecha: '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
  ver: '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
  reloj: '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  vacio: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
};

function icono(nombre, tam = 20) {
  return `<svg viewBox="0 0 24 24" width="${tam}" height="${tam}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONOS[nombre] || ""}</svg>`;
}

// ------------------------------------------------------------ Utilidades
/** Escapa texto antes de ponerlo dentro de HTML (evita que alguien meta <script> en un nombre). */
function esc(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function iniciales(nombre) {
  const partes = String(nombre || "?").trim().split(/\s+/);
  return ((partes[0] || "?")[0] + (partes[1] ? partes[1][0] : "")).toUpperCase();
}

function formatearFecha(iso) {
  if (!iso) return "—";
  const fecha = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z"); // el servidor guarda en UTC
  return fecha.toLocaleString("es-HN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function insignia(texto, color) {
  return `<span class="insignia i-${color}">${esc(texto)}</span>`;
}

/** Color de la insignia según la situación académica o el estado de la matrícula. */
function insigniaEstado(estado) {
  const colores = { Aprobado: "verde", Reprobado: "rojo", "En proceso": "amarillo", activa: "verde", retirada: "gris" };
  return insignia(estado, colores[estado] || "azul");
}

function crearElemento(html) {
  const plantilla = document.createElement("template");
  plantilla.innerHTML = html.trim();
  return plantilla.content.firstElementChild;
}

function esperar(ms) {
  return new Promise((resolver) => setTimeout(resolver, ms));
}

/** Evita llamar a la API en cada tecla: espera a que la persona deje de escribir. */
function conRetardo(funcion, ms = 300) {
  let temporizador;
  return (...args) => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => funcion(...args), ms);
  };
}

// ------------------------------------------------------------------- API
class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje);
    this.estado = estado;
  }
}

/** Convierte lo que responde FastAPI en un mensaje legible. */
function mensajeDeError(datos) {
  if (!datos || !datos.detail) return "Ocurrió un error inesperado";
  if (typeof datos.detail === "string") return datos.detail;
  // Errores de validación de Pydantic (422): lista de {loc, msg}
  return datos.detail
    .map((e) => `${(e.loc || []).slice(-1)[0] || "dato"}: ${e.msg}`)
    .join(" · ");
}

/**
 * Llama a la API. Devuelve el JSON, o lanza ErrorApi con un mensaje en español.
 *   await api("/estudiantes")
 *   await api("/estudiantes", { metodo: "POST", cuerpo: {...} })
 *   await api("/estudiantes", { params: { buscar: "ana" } })
 */
async function api(url, { metodo = "GET", cuerpo, params } = {}) {
  if (params) {
    const consulta = new URLSearchParams();
    Object.entries(params).forEach(([clave, valor]) => {
      if (valor !== undefined && valor !== null && valor !== "") consulta.append(clave, valor);
    });
    if ([...consulta].length) url += "?" + consulta.toString();
  }
  let respuesta;
  try {
    respuesta = await fetch(url, {
      method: metodo,
      credentials: "same-origin", // envía la cookie de sesión
      headers: { "Content-Type": "application/json", "X-CSRF-Token": cookieCSRF() },
      body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
    });
  } catch (e) {
    throw new ErrorApi("No se pudo conectar con la API. ¿Está corriendo uvicorn?", 0);
  }
  if (respuesta.status === 401) {
    window.location.href = "/login";
    throw new ErrorApi("Sesión expirada", 401);
  }
  let datos = null;
  try { datos = await respuesta.json(); } catch (e) { /* respuesta sin cuerpo */ }
  if (!respuesta.ok) throw new ErrorApi(mensajeDeError(datos), respuesta.status);
  return datos;
}

// ---------------------------------------------------------------- Avisos
function avisar(texto, tipo = "ok") {
  const contenedor = document.getElementById("avisos");
  const aviso = crearElemento(`<div class="aviso ${tipo}">${icono(tipo === "ok" ? "ok" : "alerta", 18)}<span>${esc(texto)}</span></div>`);
  contenedor.appendChild(aviso);
  setTimeout(() => aviso.remove(), tipo === "ok" ? 3200 : 5500);
}

// ----------------------------------------------------------------- Modales
let numeroModal = 0;
function abrirModal({ titulo, cuerpo, pie = "", grande = false }) {
  const idTitulo = `titulo-modal-${++numeroModal}`;
  const fondo = crearElemento(`
    <div class="fondo-modal">
      <div class="modal ${grande ? "grande" : ""}" role="dialog" aria-modal="true" aria-labelledby="${idTitulo}">
        <div class="modal-cab"><h3 id="${idTitulo}">${esc(titulo)}</h3><button class="btn-icono" data-cerrar aria-label="Cerrar">${icono("cerrar", 16)}</button></div>
        <div class="modal-cuerpo">${cuerpo}</div>
        ${pie ? `<div class="modal-pie">${pie}</div>` : ""}
      </div>
    </div>`);
  const focoAnterior = document.activeElement;
  const cerrar = () => { fondo.remove(); document.removeEventListener("keydown", alTeclear); const anterior=[...document.querySelectorAll(".fondo-modal")].at(-1); if(anterior) anterior.inert=false; document.querySelector(".app").inert = !!anterior; focoAnterior?.focus(); };
  const alTeclear = (e) => {
    if ([...document.querySelectorAll(".fondo-modal")].at(-1) !== fondo) return;
    if (e.key === "Escape") cerrar();
    if (e.key === "Tab") {
      const focos = [...fondo.querySelectorAll('button:not(:disabled),input:not(:disabled),select,a[href]')].filter(n=>!n.hidden);
      if (e.shiftKey && document.activeElement === focos[0]) {e.preventDefault(); focos.at(-1)?.focus();}
      else if (!e.shiftKey && document.activeElement === focos.at(-1)) {e.preventDefault(); focos[0]?.focus();}
    }
  };
  fondo.addEventListener("mousedown", (e) => { if (e.target === fondo) cerrar(); });
  fondo.querySelector("[data-cerrar]").addEventListener("click", cerrar);
  document.addEventListener("keydown", alTeclear);
  document.querySelectorAll(".fondo-modal").forEach(f=>f.inert=true);
  document.body.appendChild(fondo);
  document.querySelector(".app").inert = true;
  fondo.querySelector("button")?.focus();
  return { elemento: fondo, cerrar };
}

/** Pregunta "¿Está seguro?" y devuelve true/false. */
function confirmar(mensaje, textoBoton = "Eliminar") {
  return new Promise((resolver) => {
    const ventana = abrirModal({
      titulo: "Confirmar acción",
      cuerpo: `<p style="margin:0">${esc(mensaje)}</p>`,
      pie: `<button class="btn btn-claro" data-no>Cancelar</button><button class="btn btn-peligro" data-si>${esc(textoBoton)}</button>`,
    });
    ventana.elemento.querySelector("[data-no]").onclick = () => { ventana.cerrar(); resolver(false); };
    ventana.elemento.querySelector("[data-si]").onclick = () => { ventana.cerrar(); resolver(true); };
    ventana.elemento.querySelector("[data-cerrar]").addEventListener("click", () => resolver(false));
  });
}

// ------------------------------------------------------------ Formularios
/** Genera el HTML de un campo. tipo: text | email | number | select */
function htmlCampo(campo, valor) {
  const id = "campo-" + campo.clave;
  const ancho = campo.ancho ? " ancho" : "";
  const requerido = campo.requerido ? "required" : "";
  const ayuda = campo.ayuda ? `<div class="ayuda">${esc(campo.ayuda)}</div>` : "";
  const valorTexto = valor === null || valor === undefined ? "" : valor;
  let control;
  if (campo.tipo === "select") {
    const opciones = (campo.opcionesCargadas || [])
      .map((o) => `<option value="${esc(o.valor)}" ${String(o.valor) === String(valorTexto) ? "selected" : ""}>${esc(o.etiqueta)}</option>`)
      .join("");
    control = `<select id="${id}" name="${campo.clave}" ${requerido}>${opciones}</select>`;
  } else {
    const lista = campo.sugerencias ? `list="lista-${campo.clave}"` : "";
    const datalist = campo.sugerencias
      ? `<datalist id="lista-${campo.clave}">${campo.sugerencias.map((s) => `<option value="${esc(s)}">`).join("")}</datalist>`
      : "";
    const extra = ["min", "max", "step", "minlength", "maxlength", "placeholder"].filter((k) => campo[k] !== undefined).map((k) => `${k}="${esc(campo[k])}"`).join(" ");
    control = `<input id="${id}" name="${campo.clave}" type="${campo.tipo || "text"}" value="${esc(valorTexto)}" ${requerido} ${lista} ${extra} autocomplete="off" />${datalist}`;
  }
  return `<div class="campo${ancho}"><label for="${id}">${esc(campo.etiqueta)}${campo.requerido ? " *" : ""}</label>${control}${ayuda}</div>`;
}

/**
 * Abre una ventana con un formulario.
 *   abrirFormulario({ titulo, campos, valores, textoGuardar, alGuardar: async (datos) => {...} })
 * Si alGuardar lanza un error, se muestra dentro de la ventana y NO se cierra.
 */
async function abrirFormulario({ titulo, campos, valores = {}, textoGuardar = "Guardar", alGuardar }) {
  // Los campos "select" pueden traer sus opciones desde la API (ej. lista de docentes)
  for (const campo of campos) {
    if (campo.tipo === "select") {
      campo.opcionesCargadas = typeof campo.opciones === "function" ? await campo.opciones() : campo.opciones;
    }
  }
  const ventana = abrirModal({
    titulo,
    cuerpo: `
      <form id="form-modal" novalidate>
        <div class="mensaje-error" id="error-modal" hidden></div>
        <div class="formulario">${campos.map((c) => htmlCampo(c, valores[c.clave])).join("")}</div>
      </form>`,
    pie: `<button class="btn btn-claro" data-cancelar>Cancelar</button><button class="btn btn-primario" data-guardar>${icono("guardar", 16)} ${esc(textoGuardar)}</button>`,
  });
  const formulario = ventana.elemento.querySelector("#form-modal");
  const cajaError = ventana.elemento.querySelector("#error-modal");
  const botonGuardar = ventana.elemento.querySelector("[data-guardar]");
  ventana.elemento.querySelector("[data-cancelar]").onclick = ventana.cerrar;
  const primero = formulario.querySelector("input, select");
  if (primero) primero.focus();

  const enviar = async () => {
    cajaError.hidden = true;
    if (!formulario.reportValidity()) return;
    // Convertimos lo escrito en un objeto {clave: valor}, con el tipo correcto
    const datos = {};
    for (const campo of campos) {
      const valorCampo = formulario.elements[campo.clave].value;
      const crudo = campo.tipo === "password" ? valorCampo : valorCampo.trim();
      if (campo.tipo === "number" || campo.numero) datos[campo.clave] = crudo === "" ? null : Number(crudo);
      else datos[campo.clave] = crudo === "" && campo.opcional ? null : crudo;
    }
    botonGuardar.disabled = true;
    try {
      await alGuardar(datos);
      ventana.cerrar();
    } catch (error) {
      cajaError.textContent = error.message;
      cajaError.hidden = false;
      botonGuardar.disabled = false;
    }
  };
  botonGuardar.onclick = enviar;
  formulario.addEventListener("submit", (e) => { e.preventDefault(); enviar(); });
}

// ------------------------------------------------------------------ Tablas
/**
 * Crea una tabla con paginación dentro de `contenedor`.
 *   const tabla = crearTabla(contenedor, {
 *     columnas: [{ titulo: "Nombre", clave: "nombre" }, { titulo: "Estado", render: (f) => insigniaEstado(f.estado) }],
 *     acciones: [{ icono: "editar", titulo: "Editar", clase: "", alClick: (fila, tr) => {...} }],
 *     vacio: "No hay registros",
 *   });
 *   tabla.mostrar(arregloDeFilas);
 * `render` devuelve HTML: acuérdate de usar esc() con los datos de texto.
 */
function crearTabla(contenedor, { columnas, acciones = [], vacio = "No hay registros para mostrar", porPagina = 10 }) {
  let filas = [];
  let pagina = 1;

  function dibujar() {
    const paginas = Math.max(Math.ceil(filas.length / porPagina), 1);
    pagina = Math.min(pagina, paginas);
    const visibles = filas.slice((pagina - 1) * porPagina, pagina * porPagina);

    if (!filas.length) {
      contenedor.innerHTML = `<div class="vacio">${icono("vacio", 44)}<div>${esc(vacio)}</div></div>`;
      return;
    }
    const encabezados = columnas.map((c) => `<th class="${c.clase || ""}">${esc(c.titulo)}</th>`).join("") + (acciones.length ? '<th class="der">Acciones</th>' : "");
    const cuerpo = visibles
      .map((fila, i) => {
        const celdas = columnas.map((c) => `<td class="${c.clase || ""}">${c.render ? c.render(fila) : esc(fila[c.clave])}</td>`).join("");
        const botones = acciones
          .filter((a) => !a.mostrarSi || a.mostrarSi(fila))
          .map((a, j) => `<button class="btn-icono ${a.clase || ""}" data-accion="${acciones.indexOf(a)}" title="${esc(a.titulo)}" aria-label="${esc(a.titulo)}">${icono(a.icono, 16)}</button>`)
          .join("");
        return `<tr data-fila="${i}">${celdas}${acciones.length ? `<td><div class="acciones">${botones}</div></td>` : ""}</tr>`;
      })
      .join("");

    const desde = (pagina - 1) * porPagina + 1;
    const hasta = Math.min(pagina * porPagina, filas.length);
    const botonesPagina = [];
    for (let p = 1; p <= paginas; p++) {
      if (paginas > 7 && p !== 1 && p !== paginas && Math.abs(p - pagina) > 1) {
        if (botonesPagina[botonesPagina.length - 1] !== "…") botonesPagina.push("…");
        continue;
      }
      botonesPagina.push(p);
    }
    contenedor.innerHTML = `
      <div class="tabla-contenedor"><table class="tabla"><thead><tr>${encabezados}</tr></thead><tbody>${cuerpo}</tbody></table></div>
      <div class="paginacion">
        <span>Mostrando ${desde}–${hasta} de ${filas.length}</span>
        <div class="botones">
          <button data-ir="${pagina - 1}" ${pagina === 1 ? "disabled" : ""}>‹</button>
          ${botonesPagina.map((p) => (p === "…" ? "<span>…</span>" : `<button data-ir="${p}" class="${p === pagina ? "actual" : ""}">${p}</button>`)).join("")}
          <button data-ir="${pagina + 1}" ${pagina === paginas ? "disabled" : ""}>›</button>
        </div>
      </div>`;

    contenedor.querySelectorAll("[data-ir]").forEach((b) => (b.onclick = () => { pagina = Number(b.dataset.ir); dibujar(); }));
    contenedor.querySelectorAll("[data-accion]").forEach((b) => {
      b.onclick = () => {
        const tr = b.closest("tr");
        acciones[Number(b.dataset.accion)].alClick(visibles[Number(tr.dataset.fila)], tr);
      };
    });
  }

  return {
    mostrar(nuevasFilas, { conservarPagina = false } = {}) {
      filas = nuevasFilas;
      if (!conservarPagina) pagina = 1;
      dibujar();
    },
    get filas() { return filas; },
    redibujar: dibujar,
  };
}

// ---------------------------------------------------------- Módulos y router
const MODULOS = [];

/** Cada archivo modulo_*.js llama a esta función una vez. */
function registrarModulo(modulo) {
  if (esAdmin() || !["usuarios", "datos"].includes(modulo.id)) MODULOS.push(modulo);
}

const GRUPOS = { principal: "Principal", academico: "Académico", analisis: "Análisis", admin: "Administración" };

function moduloActual() {
  const id = (location.hash.replace(/^#\/?/, "") || "inicio").split("?")[0];
  return MODULOS.find((m) => m.id === id) || MODULOS[0];
}

function guardarReciente(modulo) {
  if (modulo.id === "inicio") return;
  try {
    const lista = JSON.parse(localStorage.getItem("matricula_recientes") || "[]").filter((id) => id !== modulo.id);
    lista.unshift(modulo.id);
    localStorage.setItem("matricula_recientes", JSON.stringify(lista.slice(0, 5)));
  } catch (e) { /* si el navegador no deja guardar, no pasa nada */ }
}

function leerRecientes() {
  try { return JSON.parse(localStorage.getItem("matricula_recientes") || "[]"); } catch (e) { return []; }
}

async function mostrarModulo() {
  const modulo = moduloActual();
  document.querySelectorAll(".nav-item").forEach((a) => a.classList.toggle("activo", a.dataset.id === modulo.id));
  document.getElementById("miga-grupo").textContent = GRUPOS[modulo.grupo];
  document.getElementById("miga-titulo").textContent = modulo.titulo;
  document.title = `${modulo.titulo} · Sistema de Matrícula`;
  document.getElementById("lateral").classList.remove("abierto");
  guardarReciente(modulo);

  const vista = document.getElementById("vista");
  vista.innerHTML = `<div class="cargando">Cargando…</div>`;
  window.scrollTo(0, 0);
  try {
    vista.innerHTML = "";
    await modulo.render(vista);
  } catch (error) {
    vista.innerHTML = `<div class="tarjeta tarjeta-cuerpo"><div class="mensaje-error" style="margin:0">${esc(error.message)}</div></div>`;
  }
}

function iniciarAplicacion() {
  // Menú lateral, agrupado
  const navegacion = document.getElementById("navegacion");
  Object.keys(GRUPOS).forEach((grupo) => {
    const modulos = MODULOS.filter((m) => m.grupo === grupo);
    if (!modulos.length) return;
    navegacion.insertAdjacentHTML("beforeend", `<div class="nav-grupo">${GRUPOS[grupo]}</div>`);
    modulos.forEach((m) => {
      navegacion.insertAdjacentHTML("beforeend", `<a class="nav-item" href="#/${m.id}" data-id="${m.id}">${icono(m.icono, 19)}<span>${esc(m.titulo)}</span></a>`);
    });
  });

  document.getElementById("boton-menu").innerHTML = icono("menu", 18);
  document.getElementById("boton-menu").onclick = () => document.getElementById("lateral").classList.toggle("abierto");
  const botonSalir = document.getElementById("boton-salir");
  botonSalir.innerHTML = `${icono("salir", 15)} Salir`;
  botonSalir.onclick = async () => {
    try { await api("/auth/logout", { metodo: "POST" }); } catch (e) { /* aunque falle, volvemos al login */ }
    window.location.href = "/login";
  };

  window.addEventListener("hashchange", mostrarModulo);
  mostrarModulo();
}

// ------------------------------------------------------- CRUD genérico
/**
 * Arma una pantalla completa de "lista + buscar + crear + editar + eliminar" a partir
 * de una configuración. Estudiantes, Docentes y Cursos usan esta misma función:
 * lo único que cambia es la configuración.
 *
 *   configuracion = {
 *     singular: "estudiante", plural: "estudiantes", articulo: "el",
 *     descripcion: "texto bajo el título",
 *     ruta: "/estudiantes",                 // endpoint de la API
 *     columnas: [...],                      // ver crearTabla()
 *     campos: [...],                        // ver abrirFormulario()
 *     acciones: [...],                      // acciones extra por fila (opcional)
 *     nombreFila: (fila) => "texto",        // para el mensaje de "¿eliminar?"
 *   }
 */
async function renderCrud(contenedor, cfg) {
  contenedor.innerHTML = `
    <div class="cabecera">
      <div><h2>${esc(cfg.titulo)}</h2><p>${esc(cfg.descripcion)}</p></div>
      <button class="btn btn-primario" id="crud-nuevo">${icono("mas", 16)} Nuevo ${esc(cfg.singular)}</button>
    </div>
    <div class="tarjeta">
      <div class="herramientas">
        <div class="buscador">${icono("buscar", 16)}<input type="search" id="crud-buscar" placeholder="Buscar ${esc(cfg.plural)}…" /></div>
        <span class="total" id="crud-total"></span>
      </div>
      <div id="crud-tabla"></div>
    </div>`;

  const total = contenedor.querySelector("#crud-total");
  const tabla = crearTabla(contenedor.querySelector("#crud-tabla"), {
    columnas: cfg.columnas,
    vacio: `Todavía no hay ${cfg.plural}. Use el botón "Nuevo ${cfg.singular}".`,
    acciones: [
      ...(cfg.acciones || []),
      ...(esAdmin() ? [
      { icono: "editar", titulo: "Editar", alClick: (fila) => editar(fila) },
      { icono: "borrar", titulo: "Eliminar", clase: "peligro", alClick: (fila) => eliminar(fila) },
      ] : []),
    ],
  });

  async function cargar({ conservarPagina = false } = {}) {
    const texto = contenedor.querySelector("#crud-buscar").value.trim();
    const filas = await api(cfg.ruta, { params: { buscar: texto } });
    total.textContent = `${filas.length} ${filas.length === 1 ? cfg.singular : cfg.plural}`;
    tabla.mostrar(filas, { conservarPagina });
  }

  function crear() {
    return abrirFormulario({
      titulo: `Nuevo ${cfg.singular}`,
      campos: cfg.campos,
      textoGuardar: "Crear",
      alGuardar: async (datos) => {
        await api(cfg.ruta, { metodo: "POST", cuerpo: datos });
        avisar(`${cfg.singular[0].toUpperCase() + cfg.singular.slice(1)} creado correctamente`);
        await cargar();
      },
    });
  }

  function editar(fila) {
    return abrirFormulario({
      titulo: `Editar ${cfg.singular}`,
      campos: cfg.campos,
      valores: fila,
      textoGuardar: "Guardar cambios",
      alGuardar: async (datos) => {
        await api(`${cfg.ruta}/${fila.id}`, { metodo: "PUT", cuerpo: datos });
        avisar("Cambios guardados");
        await cargar({ conservarPagina: true });
      },
    });
  }

  async function eliminar(fila) {
    if (!(await confirmar(`¿Eliminar ${cfg.articulo} ${cfg.singular} "${cfg.nombreFila(fila)}"? Esta acción no se puede deshacer.`))) return;
    try {
      await api(`${cfg.ruta}/${fila.id}`, { metodo: "DELETE" });
      avisar(`${cfg.singular[0].toUpperCase() + cfg.singular.slice(1)} eliminado`);
      await cargar({ conservarPagina: true });
    } catch (error) {
      avisar(error.message, "error"); // ej. 409: tiene matrículas registradas
    }
  }

  contenedor.querySelector("#crud-nuevo").hidden = !esAdmin();
  contenedor.querySelector("#crud-nuevo").onclick = crear;
  contenedor.querySelector("#crud-buscar").addEventListener("input", conRetardo(() => cargar().catch((e) => avisar(e.message, "error"))));
  await cargar();
}
