// ==========================================
// 1. LÓGICA DEL MODAL (NUEVA MASCOTA) - INTACTA
// ==========================================
const overlay       = document.getElementById('modalNuevaMascota');
const btnAbrir      = document.getElementById('btnNuevaMascota');
const btnCerrar     = document.getElementById('btnCerrarModal');
const btnCancelar   = document.getElementById('btnCancelar');
const form          = document.getElementById('formNuevaMascota');

if (btnAbrir) {
    btnAbrir.addEventListener('click', () => {
        overlay.classList.add('visible');
        document.body.style.overflow = 'hidden';
    });
}

function cerrarModal() {
    overlay.classList.remove('visible');
    document.body.style.overflow = '';
    form.reset();
}

if (btnCerrar) btnCerrar.addEventListener('click', cerrarModal);
if (btnCancelar) btnCancelar.addEventListener('click', cerrarModal);

overlay?.addEventListener('click', (e) => {
    if (e.target === overlay) cerrarModal();
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('visible')) cerrarModal();
});

form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    try {
        const response = await fetch('/mascotas/nueva/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        });

        const data = await response.json();

        if (data.ok) {
            cerrarModal();
            mostrarToast('Mascota registrada correctamente');
            setTimeout(() => location.reload(), 1000);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al guardar:', error);
    }
});

// ==========================================
// 2. LÓGICA DE FILTROS AJUSTADA (Buscador, Especie, Raza, Estado)
// ==========================================
const inputBusqueda = document.getElementById('mascotaSearch');
const selEspecie    = document.getElementById('filterEspecie');
const selRaza       = document.getElementById('filterRaza');
const selEstado     = document.getElementById('filterEstado');

function filtrarTabla() {
    const filas = document.querySelectorAll('#mascotasBody tr');
    
    // Obtenemos valores de los filtros
    const busqueda  = inputBusqueda.value.toLowerCase();
    const espEleg   = selEspecie.value;
    const razaEleg  = selRaza.value;
    const estEleg   = selEstado ? selEstado.value.toLowerCase() : "";

    filas.forEach(fila => {
        // Datos para búsqueda de texto (Nombre, Propietario, Folio)
        const contenidoTexto = fila.innerText.toLowerCase();
        
        // Datos de atributos
        const fEsp  = fila.getAttribute('data-especie') || "";
        const fRaza = fila.getAttribute('data-raza') || "";
        // El estado lo sacamos de un atributo o buscamos el texto "Activo/Inactivo" en la fila
        const fEst  = contenidoTexto.includes('activo') ? 'activo' : 'inactivo';

        // Lógica de coincidencia cruzada
        const coincideBusqueda = contenidoTexto.includes(busqueda);
        const coincideEsp      = (espEleg === "" || fEsp === espEleg);
        const coincideRaza     = (razaEleg === "" || fRaza === razaEleg);
        const coincideEstado   = (estEleg === "" || fEst === estEleg);

        // Se muestra solo si cumple TODOS los filtros activos
        if (coincideBusqueda && coincideEsp && coincideRaza && coincideEstado) {
            fila.style.display = "";
        } else {
            fila.style.display = "none";
        }
    });
}

// Listeners para los filtros
inputBusqueda?.addEventListener('input', filtrarTabla);
if (selEstado) selEstado.addEventListener('change', filtrarTabla);

if (selEspecie) {
    selEspecie.addEventListener('change', function() {
        const esp = this.value;
        selRaza.value = ""; // Resetear raza al cambiar especie

        Array.from(selRaza.options).forEach(opt => {
            if (opt.value === "") {
                opt.style.display = "";
            } else {
                const espOpt = opt.getAttribute('data-especie');
                const mostrar = (esp === "" || espOpt === esp);
                opt.style.display = mostrar ? "" : "none";
                opt.disabled = !mostrar;
            }
        });
        filtrarTabla();
    });
}

if (selRaza) {
    selRaza.addEventListener('change', filtrarTabla);
}

// ==========================================
// 3. NOTIFICACIÓN VISUAL - INTACTA
// ==========================================
function mostrarToast(mensaje) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = mensaje;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.backgroundColor = '#10B981';
    toast.style.color = 'white';
    toast.style.padding = '10px 20px';
    toast.style.borderRadius = '8px';
    toast.style.zIndex = '1000';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}