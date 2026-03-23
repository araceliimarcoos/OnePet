// Modal para historial



// ===== BÚSQUEDA =====
document.getElementById('consultasSearch').addEventListener('input', filtrar);
document.getElementById('filterEstado').addEventListener('change', filtrar);

function filtrar() {
    const q       = document.getElementById('consultasSearch').value.toLowerCase();
    const estado  = document.getElementById('filterEstado').value;

    document.querySelectorAll('#consultasBody tr').forEach(row => {
        const texto     = row.textContent.toLowerCase();
        const rowEstado = row.dataset.estado || '';

        const okTexto   = texto.includes(q);
        const okEstado  = !estado || rowEstado === estado;

        row.style.display = (okTexto && okEstado) ? '' : 'none';
    });
}