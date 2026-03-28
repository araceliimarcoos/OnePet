const overlay       = document.getElementById('modalNuevaEspecie');
const btnAbrir      = document.getElementById('btnNuevaEspecie');
const btnCerrar     = document.getElementById('btnCerrarModal');
const btnCancelar   = document.getElementById('btnCancelar');
const form          = document.getElementById('formNuevaEspecie');

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