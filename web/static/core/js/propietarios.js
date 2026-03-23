const overlay       = document.getElementById('modalNuevoPropietario');
const btnAbrir      = document.getElementById('btnNuevoPropietario');
const btnCerrar     = document.getElementById('btnCerrarModal');
const btnCancelar   = document.getElementById('btnCancelar');
const btnLimpiar    = document.getElementById('btnLimpiar');
const form          = document.getElementById('formNuevoPropietario');
const folioInput    = document.getElementById('folioAuto');

// ── Abrir modal ──
btnAbrir.addEventListener('click', () => {
    overlay.classList.add('visible');
    document.body.style.overflow = 'hidden';
});

// ── Cerrar modal ──
function cerrarModal() {
    overlay.classList.remove('visible');
    document.body.style.overflow = '';
    form.reset();
    // Restaurar el folio (reset lo borra al ser readonly en algunos browsers)
    folioInput.value = 'VCP-2024-0892';
}

btnCerrar.addEventListener('click', cerrarModal);
btnCancelar.addEventListener('click', cerrarModal);
overlay.addEventListener('click', e => { if (e.target === overlay) cerrarModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarModal(); });

// ── Limpiar campos (sin cerrar, sin tocar el folio) ──
btnLimpiar.addEventListener('click', () => {
    const folio = folioInput.value; // guardar folio
    form.reset();
    folioInput.value = folio;       // restaurar folio
});

// ── Filtro búsqueda en tabla ──
document.getElementById('propietarioSearch').addEventListener('input', filtrar);
document.getElementById('filterEstadoProp').addEventListener('change', filtrar);

function filtrar() {
    const q      = document.getElementById('propietarioSearch').value.toLowerCase();
    const estado = document.getElementById('filterEstadoProp').value;

    document.querySelectorAll('#propietariosBody tr').forEach(row => {
        const texto    = row.textContent.toLowerCase();
        const rowEst   = row.dataset.estado || '';

        const okTexto  = texto.includes(q);
        const okEstado = !estado || rowEst === estado;

        row.style.display = (okTexto && okEstado) ? '' : 'none';
    });
}

// ── Enviar formulario a Django ──
form.addEventListener('submit', async e => {
    e.preventDefault();

    const formData = new FormData(form);

    try {
        const response = await fetch('/propietarios/nuevo/', {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') }
        });

        const data = await response.json();

        if (data.ok) {
            cerrarModal();
            // TODO: mostrarToast('Propietario registrado correctamente');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al guardar:', error);
    }
});