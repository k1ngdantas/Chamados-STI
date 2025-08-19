// Scripts personalizados para o Sistema de Chamados BDA AMV

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers do Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide para alertas
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Validação de formulários
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Atualização automática de estatísticas
    if (document.getElementById('total-chamados')) {
        updateStats();
        // Atualizar a cada 30 segundos
        setInterval(updateStats, 30000);
    }

    // Animações para cards de estatísticas
    animateStatsCards();

    // Configuração de gráficos
    setupCharts();

    // Funcionalidade de busca em tabelas
    setupTableSearch();

    // Funcionalidade de filtros
    setupFilters();

    // Notificações em tempo real (simuladas)
    setupNotifications();
});

// Função para atualizar estatísticas
function updateStats() {
    fetch('/api/estatisticas')
        .then(response => response.json())
        .then(data => {
            animateCounter('total-chamados', data.total);
            animateCounter('chamados-abertos', data.aberto);
            animateCounter('chamados-andamento', data.em_andamento);
            animateCounter('chamados-resolvidos', data.resolvido);
        })
        .catch(error => {
            console.error('Erro ao carregar estatísticas:', error);
        });
}

// Função para animar contadores
function animateCounter(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const currentValue = parseInt(element.textContent) || 0;
    const increment = (targetValue - currentValue) / 20;
    let current = currentValue;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= targetValue) || 
            (increment < 0 && current <= targetValue)) {
            current = targetValue;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 50);
}

// Função para animar cards de estatísticas
function animateStatsCards() {
    const cards = document.querySelectorAll('.card.bg-primary, .card.bg-warning, .card.bg-info, .card.bg-success');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease-out';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Função para configurar gráficos
function setupCharts() {
    // Configurações globais do Chart.js
    Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
    Chart.defaults.color = '#6c757d';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
}

// Função para configurar busca em tabelas
function setupTableSearch() {
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const table = this.closest('.card').querySelector('table');
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });
}

// Função para configurar filtros
function setupFilters() {
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            const filterValue = this.value;
            const table = this.closest('.card').querySelector('table');
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                if (filterValue === '' || row.querySelector(`[data-filter="${filterValue}"]`)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    });
}

// Função para configurar notificações
function setupNotifications() {
    // Simular notificações em tempo real
    setInterval(() => {
        const random = Math.random();
        if (random < 0.1) { // 10% de chance a cada 30 segundos
            showNotification('Novo chamado criado', 'info');
        }
    }, 30000);
}

// Função para mostrar notificações
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto-remove após 5 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Função para exportar dados
function exportTableData(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let csv = [];
    const rows = table.querySelectorAll('tr');

    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            let text = cols[j].innerText.replace(/"/g, '""');
            row.push('"' + text + '"');
        }
        
        csv.push(row.join(','));
    }

    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Função para confirmar ações
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Função para formatar data
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Função para calcular tempo decorrido
function getTimeElapsed(startDate) {
    const start = new Date(startDate);
    const now = new Date();
    const diff = now - start;
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (days > 0) {
        return `${days} dia(s), ${hours} hora(s)`;
    } else if (hours > 0) {
        return `${hours} hora(s), ${minutes} minuto(s)`;
    } else {
        return `${minutes} minuto(s)`;
    }
}

// Função para atualizar tempo em tempo real
function updateRealTime() {
    const timeElements = document.querySelectorAll('[data-start-time]');
    timeElements.forEach(element => {
        const startTime = element.getAttribute('data-start-time');
        element.textContent = getTimeElapsed(startTime);
    });
}

// Atualizar tempo a cada minuto
setInterval(updateRealTime, 60000);

// Função para validar formulários específicos
function validateChamadoForm() {
    const titulo = document.getElementById('titulo').value.trim();
    const descricao = document.getElementById('descricao').value.trim();
    const categoria = document.getElementById('categoria').value;
    const prioridade = document.getElementById('prioridade').value;

    if (titulo.length < 5) {
        alert('O título deve ter pelo menos 5 caracteres.');
        return false;
    }

    if (descricao.length < 10) {
        alert('A descrição deve ter pelo menos 10 caracteres.');
        return false;
    }

    if (!categoria) {
        alert('Selecione uma categoria.');
        return false;
    }

    if (!prioridade) {
        alert('Selecione uma prioridade.');
        return false;
    }

    return true;
}

// Adicionar validação ao formulário de chamado
const chamadoForm = document.querySelector('form[action*="novo_chamado"]');
if (chamadoForm) {
    chamadoForm.addEventListener('submit', function(e) {
        if (!validateChamadoForm()) {
            e.preventDefault();
        }
    });
}

// Função para carregar dados dinamicamente
function loadData(url, targetElement, loadingText = 'Carregando...') {
    const element = document.getElementById(targetElement);
    if (!element) return;

    element.innerHTML = `<div class="text-center"><i class="fas fa-spinner fa-spin"></i> ${loadingText}</div>`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Processar dados e atualizar elemento
            element.innerHTML = processData(data);
        })
        .catch(error => {
            element.innerHTML = `<div class="alert alert-danger">Erro ao carregar dados: ${error.message}</div>`;
        });
}

// Função para processar dados (exemplo)
function processData(data) {
    // Implementar conforme necessário
    return JSON.stringify(data, null, 2);
}

// Função para mostrar/esconder elementos
function toggleElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

// Função para adicionar classe de loading
function setLoading(elementId, isLoading) {
    const element = document.getElementById(elementId);
    if (element) {
        if (isLoading) {
            element.classList.add('loading');
        } else {
            element.classList.remove('loading');
        }
    }
}

// Função para fazer requisições AJAX
function ajaxRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    return fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
}

// Função para debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Aplicar debounce na busca
const debouncedSearch = debounce(function(searchTerm) {
    // Implementar busca
    console.log('Buscando por:', searchTerm);
}, 300);

// Função para throttle
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Função para copiar para clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copiado para a área de transferência!', 'success');
    }, function(err) {
        showNotification('Erro ao copiar texto', 'danger');
    });
}

// Função para gerar PDF (simulada)
function generatePDF(elementId, filename) {
    showNotification('Gerando PDF...', 'info');
    // Implementar geração de PDF
    setTimeout(() => {
        showNotification('PDF gerado com sucesso!', 'success');
    }, 2000);
}

// Função para imprimir
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Impressão</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                </head>
                <body>
                    ${element.outerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

// Função para salvar preferências do usuário
function saveUserPreferences(preferences) {
    localStorage.setItem('userPreferences', JSON.stringify(preferences));
}

// Função para carregar preferências do usuário
function loadUserPreferences() {
    const preferences = localStorage.getItem('userPreferences');
    return preferences ? JSON.parse(preferences) : {};
}

// Função para aplicar tema
function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    saveUserPreferences({ theme: theme });
}

// Carregar tema salvo
const preferences = loadUserPreferences();
if (preferences.theme) {
    applyTheme(preferences.theme);
}

// Função para detectar dispositivo móvel
function isMobile() {
    return window.innerWidth <= 768;
}

// Ajustar interface para dispositivos móveis
if (isMobile()) {
    document.body.classList.add('mobile');
}

// Função para detectar conexão
function checkConnection() {
    if (!navigator.onLine) {
        showNotification('Você está offline. Algumas funcionalidades podem não estar disponíveis.', 'warning');
    }
}

// Verificar conexão
window.addEventListener('online', () => {
    showNotification('Conexão restaurada!', 'success');
});

window.addEventListener('offline', () => {
    showNotification('Você está offline.', 'warning');
});

// Verificar conexão inicial
checkConnection(); 