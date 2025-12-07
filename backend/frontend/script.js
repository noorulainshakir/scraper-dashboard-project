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

            // API call
            try {
                const res = await fetch(`/api/v1/services/wink-sync/start`, { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: '{}' 
                });
                const data = await res.json();
                row.dataset.jobId = data.job_id;
                row.dataset.jobId = data.job_id; // Also set for WebSocket updates
                showToast(`Service ${id} started`);
            } catch (e) {
                showToast(`Failed to start ${id}`, 'error');
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

            try {
                const res = await fetch(`/api/v1/services/wink-sync/stop/${jobId}`, { method: 'POST' });
                const data = await res.json();
                showToast(`Service ${id} stopped`);
            } catch (e) {
                showToast(`Failed to stop ${id}`, 'error');
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
        if (!jobId) { alert("No job ID found for this service."); return; }

        try {
            const res = await fetch(`/api/v1/services/wink-sync/logs/${jobId}`);
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
            if (row) {
                const statusCell = row.querySelector('.status');
                const progressCell = row.querySelector('.progress');
                
                if (statusCell) {
                    statusCell.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                    statusCell.className = `status ${data.status}`;
                }
                
                if (progressCell) {
                    progressCell.textContent = `${data.progress}%`;
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

// ===================== INIT =====================
document.addEventListener('DOMContentLoaded', () => {
    setupScheduleModal();
    setupServiceButtons();
    setupWebSocket();
});
