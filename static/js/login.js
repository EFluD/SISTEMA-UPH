
    const formulario = document.getElementById("formulario-login");
    const mensajeError = document.getElementById("mensaje-error");

    formulario.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      mensajeError.hidden = true;
      const boton = formulario.querySelector('button[type="submit"]');
      boton.disabled = true;
      boton.textContent = "Verificando…";

      const datos = {
        nombre_usuario: document.getElementById("nombre_usuario").value,
        contrasena: document.getElementById("contrasena").value,
      };

      try {
        const respuesta = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(datos),
        });

        if (!respuesta.ok) {
          const error = await respuesta.json();
          mensajeError.textContent = typeof error.detail === "string" ? error.detail : "Revise los datos ingresados";
          mensajeError.hidden = false;
          return;
        }

        // El servidor ya dejó una cookie de sesión; solo falta redirigir.
        window.location.href = "/dashboard";
      } catch (error) {
        mensajeError.textContent = "No se pudo conectar con la API";
        mensajeError.hidden = false;
      } finally {
        boton.disabled = false;
        boton.textContent = "Entrar al sistema";
      }
    });
  
