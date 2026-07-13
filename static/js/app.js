(function() {
  const state = {
    periodo: 'mensual',
    año: null,
    mes: null,
    mesesDisponibles: [],
    dataCargada: false
  };

  const DOM = {
    emptyState: document.getElementById('emptyState'),
    dashboardContent: document.getElementById('dashboardContent'),
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    fileCount: document.getElementById('fileCount'),
    uploadProgress: document.getElementById('uploadProgress'),
    emptyUploadBtn: document.getElementById('emptyUploadBtn'),
    emptyNuevaBtn: document.getElementById('emptyNuevaBtn'),
    exportPdf: document.getElementById('exportPdf'),
    exportCsv: document.getElementById('exportCsv'),
    nuevaTransaccion: document.getElementById('nuevaTransaccion'),
    nuevaTransaccionTop: document.getElementById('nuevaTransaccionTop'),
    modalOverlay: document.getElementById('modalOverlay'),
    modalTitle: document.getElementById('modalTitle'),
    modalClose: document.getElementById('modalClose'),
    modalCancel: document.getElementById('modalCancel'),
    transactionForm: document.getElementById('transactionForm'),
    txId: document.getElementById('txId'),
    txFecha: document.getElementById('txFecha'),
    txConcepto: document.getElementById('txConcepto'),
    txCategoria: document.getElementById('txCategoria'),
    txIngreso: document.getElementById('txIngreso'),
    txEgreso: document.getElementById('txEgreso'),
    kpiIngresos: document.getElementById('kpiIngresos'),
    kpiGastos: document.getElementById('kpiGastos'),
    kpiBalance: document.getElementById('kpiBalance'),
    kpiPromedio: document.getElementById('kpiPromedio'),
    monthLabel: document.getElementById('monthLabel'),
    prevMonth: document.getElementById('prevMonth'),
    nextMonth: document.getElementById('nextMonth'),
    tableBody: document.getElementById('tableBody'),
    searchInput: document.getElementById('searchInput'),
    pageSubtitle: document.getElementById('pageSubtitle'),
    periodBtns: document.querySelectorAll('.period-btn'),
    toast: document.getElementById('toast'),
  };

  const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

  function showToast(msg, type = 'info') {
    DOM.toast.textContent = msg;
    DOM.toast.className = `toast ${type} show`;
    setTimeout(() => DOM.toast.classList.remove('show'), 3000);
  }

  function formatCurrency(n) {
    return '$' + Number(n).toLocaleString('es', {minimumFractionDigits: 2, maximumFractionDigits: 2});
  }

  function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    DOM.uploadProgress.hidden = false;
    DOM.uploadProgress.querySelector('.progress-bar').style.width = '0%';
    setTimeout(() => {
      DOM.uploadProgress.querySelector('.progress-bar').style.width = '100%';
    }, 100);
    fetch('/api/upload', { method: 'POST', body: formData })
      .then(r => r.json())
      .then(data => {
        DOM.uploadProgress.hidden = true;
        if (data.error) {
          showToast('Error: ' + data.error, 'error');
          return;
        }
        showToast('Archivo cargado: ' + data.archivo, 'success');
        DOM.fileInfo.hidden = false;
        DOM.fileName.textContent = data.archivo;
        DOM.fileCount.textContent = data.total_transacciones + ' reg.';
        state.mesesDisponibles = data.meses || [];
        if (data.mes_seleccionado && data.año_seleccionado) {
          state.mes = data.mes_seleccionado;
          state.año = data.año_seleccionado;
        }
        state.dataCargada = true;
        actualizarDashboard();
      })
      .catch(err => {
        DOM.uploadProgress.hidden = true;
        showToast('Error al subir archivo', 'error');
      });
  }

  function renderCategorias(categorias) {
    const container = document.getElementById('categoriasList');
    if (!container) return;
    container.innerHTML = categorias.map(c => `<span class="categoria-chip">${c}</span>`).join('');
  }

  function cargarCategorias() {
    fetch('/api/categorias')
      .then(r => r.json())
      .then(cats => renderCategorias(cats))
      .catch(() => {});
  }

  cargarCategorias();

  function cargarDatos() {
    if (!state.dataCargada) return Promise.reject('No hay datos');
    const params = new URLSearchParams({
      periodo: state.periodo,
      año: state.año || '',
      mes: state.mes || ''
    });
    return fetch('/api/data?' + params.toString()).then(r => r.json());
  }

  function actualizarDashboard() {
    cargarDatos().then(data => {
      if (data.error) { showToast(data.error, 'error'); return; }
      DOM.emptyState.hidden = true;
      DOM.dashboardContent.hidden = false;
      DOM.kpiIngresos.textContent = formatCurrency(data.total_ingresos);
      DOM.kpiGastos.textContent = formatCurrency(data.total_egresos);
      DOM.kpiBalance.textContent = formatCurrency(data.balance);
      DOM.kpiPromedio.textContent = formatCurrency(data.promedio_diario);
      const balanceEl = DOM.kpiBalance.closest('.kpi-card').querySelector('.kpi-trend');
      if (balanceEl) {
        if (data.balance >= 0) {
          balanceEl.className = 'kpi-trend positive';
          balanceEl.innerHTML = '<i class="fas fa-arrow-up"></i> Positivo';
        } else {
          balanceEl.className = 'kpi-trend negative';
          balanceEl.innerHTML = '<i class="fas fa-arrow-down"></i> Negativo';
        }
      }
      renderDonutChart(data.gastos_por_categoria || {});
      renderLineChart(data.evolucion || []);
      renderTable(data.transacciones || []);
      DOM.pageSubtitle.textContent = `${MESES[state.mes] || ''} ${state.año || ''} · ${data.total_transacciones} transacciones`;
      DOM.monthLabel.textContent = `${MESES[state.mes] || ''} ${state.año || ''}`;
      DOM.fileCount.textContent = data.total_transacciones + ' reg.';
    }).catch(() => {});
  }

  function renderTable(transacciones) {
    const tbody = DOM.tableBody;
    tbody.innerHTML = '';
    if (!transacciones || transacciones.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--text-muted);">Sin transacciones</td></tr>';
      return;
    }
    transacciones.forEach(t => {
      const tr = document.createElement('tr');
      const catClass = (t.categoria || 'otros').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      tr.innerHTML = `
        <td>${t.fecha || ''}</td>
        <td>${t.concepto || ''}</td>
        <td><span class="category-badge ${catClass}">${t.categoria || 'Otros'}</span></td>
        <td class="amount-income">${t.ingreso > 0 ? formatCurrency(t.ingreso) : '-'}</td>
        <td class="amount-expense">${t.egreso > 0 ? formatCurrency(t.egreso) : '-'}</td>
        <td class="actions-cell">
          <button class="btn-icon btn-edit" data-id="${t.id}" title="Editar"><i class="fas fa-edit"></i></button>
          <button class="btn-icon btn-delete" data-id="${t.id}" title="Eliminar"><i class="fas fa-trash"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.btn-edit').forEach(btn => {
      btn.addEventListener('click', () => editarTransaccion(parseInt(btn.dataset.id)));
    });
    tbody.querySelectorAll('.btn-delete').forEach(btn => {
      btn.addEventListener('click', () => eliminarTransaccion(parseInt(btn.dataset.id)));
    });
  }

  function cambiarMes(delta) {
    if (!state.mesesDisponibles.length) return;
    let idx = state.mesesDisponibles.findIndex(m => m.mes === state.mes && m.año === state.año);
    idx = (idx + delta + state.mesesDisponibles.length) % state.mesesDisponibles.length;
    const m = state.mesesDisponibles[idx];
    state.mes = m.mes;
    state.año = m.año;
    actualizarDashboard();
  }

  function exportarPDF() {
    if (!state.dataCargada) { showToast('No hay datos para exportar', 'error'); return; }
    showToast('Generando PDF...', 'info');
    fetch('/api/exportar-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ periodo: state.periodo, año: state.año, mes: state.mes })
    })
    .then(r => {
      if (!r.ok) throw new Error('Error al generar PDF');
      return r.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const mesNombre = MESES[state.mes] || '';
      a.download = `Informe_Gastos_${mesNombre}_${state.año}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast('PDF descargado correctamente', 'success');
    })
    .catch(err => showToast('Error al generar PDF: ' + err.message, 'error'));
  }

  function exportarCSV() {
    if (!state.dataCargada) { showToast('No hay datos para exportar', 'error'); return; }
    fetch('/api/exportar-csv')
      .then(r => {
        if (!r.ok) throw new Error('Error al exportar CSV');
        return r.blob();
      })
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Gastos_Exportados.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('CSV descargado correctamente', 'success');
      })
      .catch(err => showToast('Error: ' + err.message, 'error'));
  }

  function abrirModal(tx = null) {
    DOM.modalOverlay.hidden = false;
    DOM.transactionForm.reset();
    DOM.txId.value = '';
    if (tx) {
      DOM.modalTitle.textContent = 'Editar Transacción';
      DOM.txId.value = tx.id;
      DOM.txFecha.value = tx.fecha || '';
      DOM.txConcepto.value = tx.concepto || '';
      DOM.txCategoria.value = tx.categoria || 'otros';
      DOM.txIngreso.value = tx.ingreso || '';
      DOM.txEgreso.value = tx.egreso || '';
    } else {
      DOM.modalTitle.textContent = 'Nueva Transacción';
      const hoy = new Date();
      const dd = String(hoy.getDate()).padStart(2, '0');
      const mm = String(hoy.getMonth() + 1).padStart(2, '0');
      const yyyy = hoy.getFullYear();
      DOM.txFecha.value = `${dd}/${mm}/${yyyy}`;
    }
  }

  function cerrarModal() {
    DOM.modalOverlay.hidden = true;
  }

  function guardarTransaccion(e) {
    e.preventDefault();
    const id = DOM.txId.value;
    const payload = {
      fecha: DOM.txFecha.value.trim(),
      concepto: DOM.txConcepto.value.trim(),
      categoria: DOM.txCategoria.value,
      ingreso: parseFloat(DOM.txIngreso.value) || 0,
      egreso: parseFloat(DOM.txEgreso.value) || 0,
    };
    if (!payload.fecha || !payload.concepto) {
      showToast('Completa todos los campos requeridos', 'error');
      return;
    }
    const url = id ? `/api/transaccion/${id}` : '/api/transaccion';
    const method = id ? 'PUT' : 'POST';
    fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
      if (data.error) { showToast('Error: ' + data.error, 'error'); return; }
      const esNueva = !id;
      showToast(esNueva ? 'Transacción creada' : 'Transacción actualizada', 'success');
      cerrarModal();
      if (esNueva && data.meses) {
        state.dataCargada = true;
        state.mesesDisponibles = data.meses;
        const ultimo = data.meses[data.meses.length - 1];
        state.mes = ultimo.mes;
        state.año = ultimo.año;
      }
      actualizarDashboard();
      if (esNueva) exportarCSV();
    })
    .catch(err => showToast('Error al guardar', 'error'));
  }

  function editarTransaccion(id) {
    if (!state.dataCargada) return;
    cargarDatos().then(data => {
      if (data.error) return;
      const tx = data.transacciones.find(t => t.id === id);
      if (tx) abrirModal(tx);
      else showToast('Transacción no encontrada', 'error');
    }).catch(() => {});
  }

  function eliminarTransaccion(id) {
    if (!confirm('¿Eliminar esta transacción?')) return;
    fetch(`/api/transaccion/${id}`, { method: 'DELETE' })
      .then(r => r.json())
      .then(data => {
        if (data.error) { showToast('Error: ' + data.error, 'error'); return; }
        showToast('Transacción eliminada', 'success');
        actualizarDashboard();
      })
      .catch(err => showToast('Error al eliminar', 'error'));
  }

  function cargarCategoriasDropdown() {
    fetch('/api/categorias')
      .then(r => r.json())
      .then(cats => {
        const sel = DOM.txCategoria;
        sel.innerHTML = cats.map(c => `<option value="${c}">${c.charAt(0).toUpperCase() + c.slice(1)}</option>`).join('');
      })
      .catch(() => {});
  }

  cargarCategoriasDropdown();

  DOM.periodBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      DOM.periodBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.periodo = btn.dataset.periodo;
      actualizarDashboard();
    });
  });

  DOM.prevMonth.addEventListener('click', () => cambiarMes(-1));
  DOM.nextMonth.addEventListener('click', () => cambiarMes(1));

  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const menuToggle = document.getElementById('menuToggle');

  function toggleSidebar() {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  }

  menuToggle.addEventListener('click', toggleSidebar);
  overlay.addEventListener('click', closeSidebar);

  DOM.uploadArea.addEventListener('click', () => { closeSidebar(); DOM.fileInput.click(); });
  DOM.emptyUploadBtn.addEventListener('click', () => DOM.fileInput.click());
  DOM.emptyNuevaBtn.addEventListener('click', () => abrirModal());

  DOM.uploadArea.addEventListener('dragover', e => {
    e.preventDefault();
    DOM.uploadArea.classList.add('dragover');
  });
  DOM.uploadArea.addEventListener('dragleave', () => {
    DOM.uploadArea.classList.remove('dragover');
  });
  DOM.uploadArea.addEventListener('drop', e => {
    e.preventDefault();
    DOM.uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });

  DOM.fileInput.addEventListener('change', () => {
    const file = DOM.fileInput.files[0];
    if (file) uploadFile(file);
  });

  DOM.exportPdf.addEventListener('click', exportarPDF);
  DOM.exportCsv.addEventListener('click', exportarCSV);
  DOM.nuevaTransaccion.addEventListener('click', () => abrirModal());
  DOM.nuevaTransaccionTop.addEventListener('click', () => abrirModal());
  DOM.modalClose.addEventListener('click', cerrarModal);
  DOM.modalCancel.addEventListener('click', cerrarModal);
  DOM.modalOverlay.addEventListener('click', e => { if (e.target === DOM.modalOverlay) cerrarModal(); });
  DOM.transactionForm.addEventListener('submit', guardarTransaccion);

  DOM.searchInput.addEventListener('input', function() {
    const q = this.value.toLowerCase();
    const rows = DOM.tableBody.querySelectorAll('tr');
    rows.forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });

  const style = document.createElement('style');
  style.textContent = `
    @media (max-width: 768px) {
      .sidebar .upload-text, .sidebar .upload-sub, .sidebar .upload-formats { display: none; }
      .sidebar .upload-area { padding: 0.8rem; }
      .sidebar .upload-icon { font-size: 1.3rem; margin-bottom: 0; }
    }
  `;
  document.head.appendChild(style);
})();
