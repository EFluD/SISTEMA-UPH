/* modulo_usuarios.js  -  Módulo 8: usuarios del sistema (login) */

registrarModulo({
  id: "usuarios",
  titulo: "Usuarios",
  grupo: "admin",
  icono: "usuarios",
  color: "c-gris",
  descripcion: "Cuentas que pueden entrar al sistema.",
  render: async (contenedor) => {
    contenedor.innerHTML = `
      <div class="cabecera">
        <div><h2>Usuarios del sistema</h2><p>Administra el acceso al campus. Las contraseñas están protegidas y nunca se muestran.</p></div>
        <button class="btn btn-primario" id="usr-nuevo">${icono("mas", 16)} Nuevo usuario</button>
      </div>
      <div class="tarjeta"><div id="usr-tabla"></div></div>`;

    const tabla = crearTabla(contenedor.querySelector("#usr-tabla"), {
      columnas: [
        { titulo: "#", clave: "id" },
        { titulo: "Usuario", render: (f) => `<div class="persona"><div class="avatar">${esc(f.nombre_usuario.slice(0, 2).toUpperCase())}</div><strong>${esc(f.nombre_usuario)}</strong></div>` },
        { titulo: "Rol", render: (f) => insignia(f.rol, f.rol === "admin" ? "azul" : "gris") },
      ],
      acciones: [
        {
          icono: "borrar",
          titulo: "Eliminar usuario",
          clase: "peligro",
          alClick: async (fila) => {
            if (!(await confirmar(`¿Eliminar al usuario "${fila.nombre_usuario}"?`))) return;
            try {
              await api(`/auth/usuarios/${fila.id}`, { metodo: "DELETE" });
              avisar("Usuario eliminado");
              await cargar();
            } catch (error) { avisar(error.message, "error"); }
          },
        },
      ],
    });
    const cargar = async () => tabla.mostrar(await api("/auth/usuarios"));

    contenedor.querySelector("#usr-nuevo").onclick = () =>
      abrirFormulario({
        titulo: "Nuevo usuario",
        textoGuardar: "Crear",
        campos: [
          { clave: "nombre_usuario", etiqueta: "Nombre de usuario", requerido: true, minlength: 3, ancho: true },
          { clave: "contrasena", etiqueta: "Contraseña", tipo: "password", requerido: true, minlength: 12 },
          { clave: "rol", etiqueta: "Rol", tipo: "select", requerido: true, opciones: [{ valor: "docente", etiqueta: "Docente (consulta)" }, { valor: "admin", etiqueta: "Administrador" }] },
        ],
        alGuardar: async (datos) => {
          await api("/auth/usuarios", { metodo: "POST", cuerpo: datos });
          avisar("Usuario creado");
          await cargar();
        },
      });
    await cargar();
  },
});
