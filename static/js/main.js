document.addEventListener('DOMContentLoaded', function() {
    // 1. Configurar la barra de búsqueda
    configurarBusqueda();
    
    // 2. Configurar los botones de WhatsApp
    configurarWhatsapp();

    // 3. Cargar la tabla de contactos al iniciar la página
    buscarContactos('');
});

// --- VARIABLES GLOBALES ---
let usuariosEncontrados = [];
let usuariosSeleccionados = [];

// ===============================================
// LÓGICA DE BÚSQUEDA DE CONTACTOS
// ===============================================
function configurarBusqueda() {
    const campoBusqueda = document.getElementById('terminoBusqueda');
    if (!campoBusqueda) return;

    let timeoutId = null;
    campoBusqueda.addEventListener('input', () => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            buscarContactos(campoBusqueda.value.trim());
        }, 300);
    });
}

async function buscarContactos(termino) {
    const listaResultados = document.getElementById('listaResultados');
    if (!listaResultados) return;
    listaResultados.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';

    try {
        const response = await fetch('/api/buscar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ termino: termino })
        });
        if (!response.ok) {
            throw new Error(`Error del servidor: ${response.statusText}`);
        }
        const data = await response.json();
        usuariosEncontrados = data.usuarios || [];
        renderizarResultados(usuariosEncontrados);
    } catch (error) {
        console.error('Error en la búsqueda:', error);
        listaResultados.innerHTML = '<div class="alert alert-danger">Error de conexión al buscar.</div>';
    }
}

function renderizarResultados(usuarios) {
    const listaResultados = document.getElementById('listaResultados');
    listaResultados.innerHTML = ''; 

    if (usuarios.length === 0) {
        listaResultados.innerHTML = '<div class="text-center py-5 text-muted col-12"><p>No se encontraron usuarios.</p></div>';
        return;
    }

    usuarios.forEach(usuario => {
        const telefono = usuario.telefono ? `<li class="list-group-item bg-transparent border-0 px-0 pt-0"><i class="bi bi-telephone-fill me-2 text-secondary"></i>${usuario.telefono}</li>` : '';
        let privilegiosHTML = '';
        if (usuario.privilegios && usuario.privilegios.length > 0) {
            privilegiosHTML = `<li class="list-group-item bg-transparent border-0 px-0 pt-0"><i class="bi bi-star-fill me-2 text-warning"></i>${usuario.privilegios.join(', ')}</li>`;
        }
        
        const isChecked = usuariosSeleccionados.some(u => u.id === usuario.id);
        const tarjetaHTML = `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 shadow-sm usuario-card ${isChecked ? 'selected' : ''}" data-user-id="${usuario.id}" onclick="toggleSeleccion(${usuario.id})">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h5 class="card-title text-primary mb-1">${usuario.nombre}</h5>
                                <small class="text-muted">${usuario.circuito} / ${usuario.congregacion}</small>
                            </div>
                            <input class="form-check-input mt-1" type="checkbox" ${isChecked ? 'checked' : ''} style="transform: scale(1.5);">
                        </div>
                        <hr>
                        <ul class="list-group list-group-flush small">
                            ${telefono}
                            ${privilegiosHTML}
                        </ul>
                    </div>
                </div>
            </div>`;
        listaResultados.insertAdjacentHTML('beforeend', tarjetaHTML);
    });
}

function toggleSeleccion(id) {
    const elemento = document.querySelector(`.usuario-card[data-user-id='${id}']`);
    if (!elemento) return;
    
    const usuario = usuariosEncontrados.find(u => u.id === id);
    if (!usuario) return;

    const index = usuariosSeleccionados.findIndex(u => u.id === id);
    if (index > -1) {
        usuariosSeleccionados.splice(index, 1);
        elemento.classList.remove('selected');
        elemento.querySelector('input').checked = false;
    } else {
        usuariosSeleccionados.push(usuario);
        elemento.classList.add('selected');
        elemento.querySelector('input').checked = true;
    }
    actualizarBotonEnvio();
}

function actualizarBotonEnvio() {
    const btn = document.getElementById('btnEnviarWhatsapp');
    if(!btn) return;
    const count = usuariosSeleccionados.length;
    btn.disabled = count === 0;
    btn.textContent = `Enviar a ${count} Seleccionado(s)`;
}

// ===============================================
// LÓGICA DE WHATSAPP
// ===============================================
function configurarWhatsapp() {
    const btnEnviar = document.getElementById('btnEnviarWhatsapp');
    if(btnEnviar) btnEnviar.addEventListener('click', enviarMensajesWhatsapp);
}

async function enviarMensajesWhatsapp() {
    const mensaje = document.getElementById('mensajeWhatsapp').value;
    if (usuariosSeleccionados.length === 0) { return alert('Por favor, selecciona al menos un contacto.'); }
    if (!mensaje.trim()) { return alert('Por favor, escribe un mensaje.'); }
    if (!confirm(`¿Estás seguro de enviar el mensaje a ${usuariosSeleccionados.length} contactos?`)) { return; }

    try {
        const response = await fetch('/api/whatsapp/enviar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuarios: usuariosSeleccionados, mensaje: mensaje })
        });
        const data = await response.json();
        alert(data.mensaje);
    } catch (error) {
        alert(`Error al enviar: ${error.message}`);
    }
}