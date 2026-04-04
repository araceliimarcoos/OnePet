const overlay       = document.getElementById('modalNuevoPropietario');
const btnAbrir      = document.getElementById('btnNuevoPropietario');
const btnCerrar     = document.getElementById('btnCerrarModal');
const btnCancelar   = document.getElementById('btnCancelar');
const form          = document.getElementById('formNuevoPropietario');
const folioInput    = document.getElementById('folioAuto');


async function cargarFolio() {
    try {
        const response = await fetch('/propietarios/folio/');
        const data = await response.json();

        folioInput.value = data.folio;
    } catch (error) {
        console.error('Error al obtener folio:', error);
    }
}
// ── Abrir modal ──
btnAbrir.addEventListener('click', () => {
    overlay.classList.add('visible');
    document.body.style.overflow = 'hidden';
    cargarFolio(); // 🔥 aquí generas el folio dinámico
});

// ── Cerrar modal ──
function cerrarModal() {
    overlay.classList.remove('visible');
    document.body.style.overflow = '';
    form.reset();
}

btnCerrar.addEventListener('click', cerrarModal);
btnCancelar.addEventListener('click', cerrarModal);
overlay.addEventListener('click', e => { if (e.target === overlay) cerrarModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarModal(); });




// ── Enviar formulario a Django ──
form.addEventListener('submit', async e => {
    e.preventDefault();

    const formData = new FormData(form);

    try {
        const response = await fetch('/propietarios/crear/', {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') }
        });

        const data = await response.json();

        if (data.ok) {
            cerrarModal();
            alert(data.message);
            location.reload();

            // TODO: mostrarToast('Propietario registrado correctamente');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error al guardar:', error);
    }
});