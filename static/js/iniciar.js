iniciarAplicacion();
document.getElementById("boton-clave").onclick = () => abrirFormulario({
  titulo:"Cambiar mi contraseña", campos:[
    {clave:"actual", etiqueta:"Contraseña actual", tipo:"password", requerido:true},
    {clave:"nueva", etiqueta:"Nueva contraseña (mínimo 12 caracteres)", tipo:"password", requerido:true, minlength:12}
  ], alGuardar:async datos => {await api("/auth/cambiar-clave",{metodo:"POST",cuerpo:datos});location.href="/login";}
});
