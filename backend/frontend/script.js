// ===================== CONFIG =====================
const CONFIG = {
    API_BASE_URL: '', // agar backend alag hai to URL yahan add karo
    TOAST_DURATION: 3000
};

// ===================== UTILITY =====================
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), CONFIG.TOAST_DURATION);
}

function formatDate(dateString) {
    if (!dateString || dateString === "Not Available") return "Not Available";
    const date = new Date(dateString);
    return date.toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.add('modal-open');
    document.body.style.overflow = "hidden";
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove('modal-open');
    document.body.style.overflow = "";
}

// ===================== SCHEDULE MODAL =====================
function setupScheduleModal() {
    const modal = document.getElementById('scheduleModal');
    const freqSelect = document.getElementById('schedFreq');
    const cronInput = document.getElementById('schedCron');
    const saveBtn = document.getElementById('saveScheduleBtn');
    const cancelBtn = document.getElementById('cancelScheduleBtn');
    const errorMsg = document.getElementById('schedError');

    if (freqSelect && cronInput) {
        freqSelect.addEventListener('change', e => {
            if (e.target.value === 'custom') {
                cronInput.disabled = false;
                cronInput.required = true;
            } else {
                cronInput.disabled = true;
                cronInput.required = false;
                cronInput.value = '';
            }
        });
    }

    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const id = document.getElementById('schedScraperId').value;
            const date = document.getElementById('schedDate').value;
            const time = document.getElementById('schedTime').value;
            const freq = freqSelect.value;
            const cron = cronInput.value;

            if (!date || !time || (freq === 'custom' && !cron)) {
                errorMsg.textContent = 'Please fill all required fields';
                return;
            }
            errorMsg.textContent = '';

            const element = document.querySelector(`tr[data-id="${id}"]`);
            if (element) {
                const nextRunP = element.querySelector('.next-run');
                if (freq === 'custom') nextRunP.textContent = `Cron: ${cron}`;
                else nextRunP.textContent = `Next Run: ${formatDate(`${date}T${time}`)}`;
            }

            closeModal('scheduleModal');
            showToast('Schedule saved');
        });
    }

    if (cancelBtn) cancelBtn.addEventListener('click', () => closeModal('scheduleModal'));

    // Close modal on clicking X
    const closeBtn = document.getElementById('closeScheduleModalBtn');
    if (closeBtn) closeBtn.addEventListener('click', () => closeModal('scheduleModal'));
}

// ===================== BUTTON EVENTS =====================
function setupServiceButtons() {
    // Start buttons
    document.querySelectorAll('.start-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const row = btn.closest('tr');
            const id = row.dataset.id;
            btn.disabled = true;
            row.querySelector('.stop-btn').disabled = false;
            row.querySelector('.status').textContent = 'Running';
            row.querySelector('.status').className = 'status running';

            // Reset progress bar for all services
            const progressBar = row.querySelector('.progress-bar');
            const progressText = row.querySelector('.progress-text');
            if (progressBar) {
                progressBar.style.width = '0%';
                progressBar.classList.remove('completed');
                progressBar.classList.add('active');
            }
            if (progressText) {
                progressText.textContent = '0%';
            }
            
            // API call - determine endpoint based on service ID
            try {
                let endpoint = '/api/v1/services/wink-sync/start'; // Default
                if (id === '002') {
                    endpoint = '/api/v1/services/wink-product-push/start'; // Future endpoint
                } else if (id === '003') {
                    endpoint = '/api/v1/services/shopify-push/start'; // Future endpoint
                }
                
                const res = await fetch(endpoint, { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: '{}' 
                });
                
                if (res.ok) {
                    const data = await res.json();
                    if (data.job_id) {
                        row.dataset.jobId = data.job_id; // Set for WebSocket updates
                    }
                    showToast(`Service ${id} started`);
                } else {
                    // If endpoint doesn't exist yet, still show UI update
                    showToast(`Service ${id} started (endpoint not implemented yet)`, 'info');
                }
            } catch (e) {
                // If API call fails, still update UI for demo purposes
                console.warn(`API endpoint not available for service ${id}:`, e);
                showToast(`Service ${id} UI updated (API endpoint pending)`, 'info');
            }
        });
    });

    // Stop buttons
    document.querySelectorAll('.stop-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const row = btn.closest('tr');
            const id = row.dataset.id;
            const jobId = row.dataset.jobId;
            if (!jobId) { alert("No job running for this service."); return; }
            btn.disabled = true;
            row.querySelector('.start-btn').disabled = false;
            row.querySelector('.status').textContent = 'Stopped';
            row.querySelector('.status').className = 'status stopped';
            
            // Reset progress bar
            const progressBar = row.querySelector('.progress-bar');
            const progressText = row.querySelector('.progress-text');
            if (progressBar) {
                progressBar.style.width = '0%';
                progressBar.classList.remove('active', 'completed');
            }
            if (progressText) {
                progressText.textContent = '0%';
            }

            // Determine endpoint based on service ID
            let endpoint = `/api/v1/services/wink-sync/stop/${jobId}`; // Default
            if (id === '002') {
                endpoint = `/api/v1/services/wink-product-push/stop/${jobId}`;
            } else if (id === '003') {
                endpoint = `/api/v1/services/shopify-push/stop/${jobId}`;
            }

            try {
                const res = await fetch(endpoint, { method: 'POST' });
                if (res.ok) {
                    const data = await res.json();
                    showToast(`Service ${id} stopped`);
                } else {
                    showToast(`Service ${id} stopped (UI only)`, 'info');
                }
            } catch (e) {
                // If API call fails, still update UI
                console.warn(`Stop endpoint not available for service ${id}:`, e);
                showToast(`Service ${id} stopped (UI only)`, 'info');
            }
        });
    });

    // Schedule buttons
    document.querySelectorAll('.schedule-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const row = btn.closest('tr');
            const id = row.dataset.id;
            document.getElementById('schedScraperId').value = id;
            document.getElementById('schedScraperName').value = row.children[1].textContent.trim();
            const now = new Date();
            document.getElementById('schedDate').value = now.toISOString().split('T')[0];
            document.getElementById('schedTime').value = now.toTimeString().slice(0, 5);
            openModal('scheduleModal');
        });
    });

   // View logs buttons
document.querySelectorAll('.view-log-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const row = btn.closest('tr');
        const jobId = row.dataset.jobId;
        const serviceId = row.dataset.id;
        if (!jobId) { alert("No job ID found for this service."); return; }

        // Determine endpoint based on service ID
        let endpoint = `/api/v1/services/wink-sync/logs/${jobId}`; // Default
        if (serviceId === '002') {
            endpoint = `/api/v1/services/wink-product-push/logs/${jobId}`;
        } else if (serviceId === '003') {
            endpoint = `/api/v1/services/shopify-push/logs/${jobId}`;
        }

        try {
            const res = await fetch(endpoint);
            const data = await res.json();

            // 👇 Debug line yahan daalo
            console.log("Logs received:", data.logs);

            const body = document.getElementById('serviceLogBody');
            body.innerHTML = '';

            // ✅ Simple string logs handle karne ke liye
            data.logs.forEach(log => {
                const div = document.createElement('div');
                div.textContent = log;   // sirf string render karo
                body.appendChild(div);
            });

            openModal('serviceLogModal');
        } catch(e) {
            showToast('Failed to fetch logs', 'error');
        }
    });
});

    // Close service log modal
    const closeLogBtn = document.getElementById('closeServiceLogModalBtn');
    if (closeLogBtn) closeLogBtn.addEventListener('click', () => closeModal('serviceLogModal'));
}

// ===================== WEBSOCKET LIVE LOGS =====================
function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log("WebSocket connected");
    };
    
    ws.onmessage = event => {
        try {
            const data = JSON.parse(event.data);
            console.log("Live update:", data);
            
            // Update job status in table if job exists
            const row = document.querySelector(`tr[data-job-id="${data.job_id}"]`);
            if (!row) {
                // Try to find by service ID if job_id not found
                const allRows = document.querySelectorAll('tr[data-id]');
                for (const r of allRows) {
                    if (r.dataset.jobId === data.job_id) {
                        row = r;
                        break;
                    }
                }
            }
            
            if (row) {
                // Update status
                const statusCell = row.querySelector('.status');
                if (statusCell) {
                    const statusText = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                    statusCell.textContent = statusText;
                    statusCell.className = `status ${data.status}`;
                }
                
                // Update progress bar
                const progressBar = row.querySelector('.progress-bar');
                const progressText = row.querySelector('.progress-text');
                if (progressBar && data.progress !== undefined) {
                    const progress = Math.min(100, Math.max(0, data.progress));
                    progressBar.style.width = `${progress}%`;
                    
                    // Update progress text
                    if (progressText) {
                        progressText.textContent = `${progress}%`;
                    }
                    
                    // Add color based on progress
                    if (progress === 100) {
                        progressBar.classList.add('completed');
                    } else if (progress > 0) {
                        progressBar.classList.add('active');
                        progressBar.classList.remove('completed');
                    } else {
                        progressBar.classList.remove('active', 'completed');
                    }
                }
            }
        } catch (e) {
            console.error("Error parsing WebSocket message:", e);
        }
    };
    
    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
    
    ws.onclose = () => {
        console.log("WebSocket disconnected, reconnecting...");
        // Reconnect after 5 seconds
        setTimeout(setupWebSocket, 5000);
    };
}

// ===================== SCRAPER LIST (INDEX PAGE) =====================
function setupScraperList() {
    const scraperList = document.getElementById('scraperList');
    if (!scraperList) return; // Not on index page
    
    // Hardcoded scrapers: Luxottica and Safilo only
    const scrapers = [
        {
            id: 'luxottica',
            name: 'Luxottica',
            description: 'Scrapes product data from Luxottica websites',
            status: 'running',
            lastRun: '2025-12-08 10:30 AM',
            nextRun: '2025-12-09 02:00 AM',
            records: 1250,
            progress: 75
        },
        {
            id: 'safilo',
            name: 'Safilo',
            description: 'Scrapes product data from Safilo websites',
            status: 'stopped',
            lastRun: '2025-12-07 02:00 AM',
            nextRun: '2025-12-09 02:00 AM',
            records: 890,
            progress: 0
        }
    ];
    
    // Clear existing content
    scraperList.innerHTML = '';
    
    // Create scraper cards
    scrapers.forEach(scraper => {
        const card = document.createElement('div');
        card.className = 'scraper-card';
        card.dataset.id = scraper.id;
        card.dataset.status = scraper.status;
        
        card.innerHTML = `
            <div class="scraper-card-header">
                <h3>${scraper.name}</h3>
                <span class="status ${scraper.status}">${scraper.status.charAt(0).toUpperCase() + scraper.status.slice(1)}</span>
            </div>
            <p class="scraper-description">${scraper.description}</p>
            <div class="scraper-stats">
                <div class="stat-item">
                    <span class="stat-label">Records</span>
                    <span class="stat-value">${scraper.records.toLocaleString()}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Last Run</span>
                    <span class="stat-value">${scraper.lastRun}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Next Run</span>
                    <span class="stat-value">${scraper.nextRun}</span>
                </div>
            </div>
            ${scraper.status === 'running' ? `
            <div class="scraper-progress">
                <div class="progress-container">
                    <div class="progress-bar active" style="width: ${scraper.progress}%">
                        <span class="progress-text">${scraper.progress}%</span>
                    </div>
                </div>
            </div>
            ` : ''}
            <div class="scraper-actions">
                <button class="start-btn" ${scraper.status === 'running' ? 'disabled' : ''}>Start</button>
                <button class="stop-btn" ${scraper.status === 'stopped' ? 'disabled' : ''}>Stop</button>
                <button class="view-details-btn">View Details</button>
            </div>
        `;
        
        scraperList.appendChild(card);
    });
    
    // Add event listeners to scraper cards
    setupScraperCardButtons();
}

function setupScraperCardButtons() {
    // Start buttons on scraper cards
    document.querySelectorAll('#scraperList .start-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const card = btn.closest('.scraper-card');
            const id = card.dataset.id;
            btn.disabled = true;
            card.querySelector('.stop-btn').disabled = false;
            card.querySelector('.status').textContent = 'Running';
            card.querySelector('.status').className = 'status running';
            card.dataset.status = 'running';
            
            // Show progress bar if not exists
            let progressContainer = card.querySelector('.scraper-progress');
            if (!progressContainer) {
                progressContainer = document.createElement('div');
                progressContainer.className = 'scraper-progress';
                progressContainer.innerHTML = `
                    <div class="progress-container">
                        <div class="progress-bar active" style="width: 0%">
                            <span class="progress-text">0%</span>
                        </div>
                    </div>
                `;
                card.querySelector('.scraper-actions').before(progressContainer);
            }
            
            showToast(`Scraper ${id} started`);
        });
    });
    
    // Stop buttons on scraper cards
    document.querySelectorAll('#scraperList .stop-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const card = btn.closest('.scraper-card');
            const id = card.dataset.id;
            btn.disabled = true;
            card.querySelector('.start-btn').disabled = false;
            card.querySelector('.status').textContent = 'Stopped';
            card.querySelector('.status').className = 'status stopped';
            card.dataset.status = 'stopped';
            
            // Remove progress bar
            const progressContainer = card.querySelector('.scraper-progress');
            if (progressContainer) {
                progressContainer.remove();
            }
            
            showToast(`Scraper ${id} stopped`);
        });
    });
    
    // View details buttons
    document.querySelectorAll('#scraperList .view-details-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const card = btn.closest('.scraper-card');
            const id = card.dataset.id;
            // Navigate to services page or show details
            window.location.href = 'services.html';
        });
    });
}

// ===================== INIT =====================
document.addEventListener('DOMContentLoaded', () => {
    setupScraperList(); // Populate scraper list on index page
    setupScheduleModal();
    setupServiceButtons();
    setupWebSocket();
});
