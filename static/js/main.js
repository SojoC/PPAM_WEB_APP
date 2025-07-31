/**
 * PPAM Web v5.0 - Lógica del Frontend
 * Conecta la interfaz con la API de Flask.
 */

// Se ejecuta cuando todo el contenido de la página se ha cargado.
document.addEventListener('DOMContentLoaded', function() {
    
    // Referencias a los elementos importantes del HTML.
    const campoBusqueda = document.getElementById('terminoBusqueda');
    const listaResultados = document.getElementById('listaResultados');
    
    // Si no encontramos los elementos, no continuamos.
    if (!campoBusqueda || !listaResultados) {
        console.error("Error: No se encontraron elementos necesarios (campo de búsqueda o lista de resultados).");
        return;
    }

    let timeoutId = null; // Variable para controlar el tiempo de espera al escribir.

    // Añadimos un "escuchador" que se activa cada vez que el usuario escribe algo.
    campoBusqueda.addEventListener('input', () => {
        // Limpiamos cualquier búsqueda anterior que estuviera esperando.
        clearTimeout(timeoutId);
        
        // Esperamos 300 milisegundos después de que el usuario deje de escribir para buscar.
        // Esto evita hacer una llamada a la API por cada letra que se presiona.
        timeoutId = setTimeout(() => {
            const termino = campoBusqueda.value.trim();
            buscarContactos(termino);
        }, 300);
    });
    
    // Realizamos una búsqueda inicial vacía para cargar todos los contactos al inicio.
    buscarContactos(''); 
});


/**
 * Función asíncrona que se comunica con la API del backend para buscar contactos.
 * @param {string} termino - El texto a buscar.
 */
async function buscarContactos(termino) {
    const listaResultados = document.getElementById('listaResultados');
    
    // Mostramos un indicador de carga.
    listaResultados.innerHTML = `
        <div class="text-center py-5 text-muted">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Buscando...</span>
            </div>
            <p class="mt-2">Buscando '${termino}'...</p>
        </div>`;

    try {
        // Hacemos la llamada a nuestra API usando fetch.
        const response = await fetch('/api/buscar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ termino: termino }) // Enviamos el término en formato JSON.
        });

        if (!response.ok) {
            throw new Error(`Error del servidor: ${response.statusText}`);
        }

        const data = await response.json(); // Convertimos la respuesta a JSON.
        renderizarResultados(data.usuarios); // Llamamos a la función para "dibujar" los resultados.

    } catch (error) {
        console.error('Error en la búsqueda:', error);
        // Mostramos un mensaje de error amigable en la pantalla.
        listaResultados.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <strong>Error de Conexión:</strong> No se pudo comunicar con el servidor.
                 Asegúrate de que la aplicación (\`python app.py\`) esté ejecutándose.
            </div>`;
    }
}

/**
 * "Dibuja" las tarjetas de los contactos en la página.
 * @param {Array} usuarios - Una lista de los contactos encontrados.
 */
function renderizarResultados(usuarios) {
    const listaResultados = document.getElementById('listaResultados');
    
    // Limpiamos los resultados anteriores.
    listaResultados.innerHTML = ''; 

    // Si la lista de usuarios está vacía, mostramos un mensaje.
    if (!usuarios || usuarios.length === 0) {
        listaResultados.innerHTML = `
            <div class="text-center py-5 text-muted">
                <i class="bi bi-person-x-fill fs-1"></i>
                <h5 class="mt-3">No se encontraron contactos</h5>
                <p>Intenta con otro término de búsqueda.</p>
            </div>`;
        return;
    }

    // Por cada usuario en la lista, creamos una tarjeta HTML.
    usuarios.forEach(usuario => {
        const tarjetaHTML = `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title text-primary">${usuario.nombre}</h5>
                        <p class="card-text mb-1">
                            <strong><i class="bi bi-telephone-fill text-secondary"></i> Teléfono:</strong> ${usuario.telefono || 'No disponible'}
                        </p>
                        <p class="card-text mb-1">
                            <strong><i class="bi bi-geo-alt-fill text-secondary"></i> Circuito:</strong> ${usuario.circuito || 'No disponible'}
                        </p>
                        <p class="card-text">
                            <strong><i class="bi bi-house-door-fill text-secondary"></i> Congregación:</strong> ${usuario.congregacion || 'No disponible'}
                        </p>
                    </div>
                </div>
            </div>`;
        
        // Añadimos la tarjeta recién creada al contenedor de resultados.
        listaResultados.insertAdjacentHTML('beforeend', tarjetaHTML);
    });
}