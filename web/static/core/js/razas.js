
// ----------------------------- MODAL RAZAS ----------------------------- //
const overlayRaza = document.getElementById('modalNuevaRaza');
const btnAbrirRaza = document.getElementById('btnNuevaRaza');
const btnCerrarRaza = document.getElementById('btnCerrarModalRaza');
const btnCancelarRaza = document.getElementById('btnCancelarRaza');
const formRaza = document.getElementById('formNuevaRaza');

function cerrarModalRaza() {
    if (!overlayRaza || !formRaza) return;
    overlayRaza.classList.remove('visible');
    document.body.style.overflow = '';
    formRaza.reset();
}

if (btnAbrirRaza) {
    btnAbrirRaza.addEventListener('click', () => {
        overlayRaza.classList.add('visible');
        document.body.style.overflow = 'hidden';
    });
}

if (btnCerrarRaza) btnCerrarRaza.addEventListener('click', cerrarModalRaza);
if (btnCancelarRaza) btnCancelarRaza.addEventListener('click', cerrarModalRaza);

overlayRaza?.addEventListener('click', (e) => {
    if (e.target === overlayRaza) cerrarModalRaza();
});

document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (overlayRaza?.classList.contains('visible')) cerrarModalRaza();
});
