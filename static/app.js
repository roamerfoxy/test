const API_URL = ""; 
let currentHeight = 0;

// Poll status every second
setInterval(fetchStatus, 1000);
fetchPresets();

async function fetchStatus() {
    try {
        const response = await fetch(`${API_URL}/desk/`);
        const data = await response.json();
        
        currentHeight = data.current_height;
        
        document.getElementById('current-height').innerText = data.current_height;
        document.getElementById('target-height').innerText = `Target: ${data.target_height}`;
        
        // Simple health check inference
        const statusEl = document.getElementById('connection-status');
        statusEl.innerText = "Connected";
        statusEl.className = "status connected";
        
    } catch (error) {
        const statusEl = document.getElementById('connection-status');
        statusEl.innerText = "Disconnected";
        statusEl.className = "status disconnected";
    }
}

async function fetchPresets() {
    const response = await fetch(`${API_URL}/presets/`);
    const data = await response.json();
    
    const grid = document.getElementById('presets-grid');
    grid.innerHTML = '';
    
    Object.values(data).forEach(preset => {
        const card = document.createElement('div');
        card.className = 'preset-card';
        
        card.innerHTML = `
            <div class="preset-info" onclick="applyPreset('${preset.name}')">
                <strong>${preset.name}</strong>
                <span>${preset.height}mm</span>
            </div>
            <div class="preset-actions-row">
                <button class="action-btn update" onclick="updatePreset('${preset.name}')">Update</button>
                <button class="action-btn delete" onclick="deletePreset('${preset.name}')">Delete</button>
            </div>
        `;
        
        grid.appendChild(card);
    });
}

async function applyPreset(name) {
    await fetch(`${API_URL}/desk/preset`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name })
    });
    fetchStatus();
}

async function updatePreset(name) {
    if (!confirm(`Update '${name}' to current height (${currentHeight}mm)?`)) return;
    
    await fetch(`${API_URL}/presets/${name}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ height: currentHeight })
    });
    fetchPresets();
}

async function deletePreset(name) {
    if (!confirm(`Delete preset '${name}'?`)) return;
    
    await fetch(`${API_URL}/presets/${name}`, {
        method: 'DELETE'
    });
    fetchPresets();
}

async function startMove(delta) {
    // For manual move, we just set target = current + delta
    const target = currentHeight + delta;
    await fetch(`${API_URL}/desk/height`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ height: target })
    });
    fetchStatus();
}

function stopMove() {
    // Optional: trigger stop endpoint if we implements one
    // For now, startMove just does small increments so "stop" is natural
}

async function stopDesk() {
     // We don't have a dedicated STOP endpoint in API yet, 
     // but setting height to current height usually stops it
    await fetch(`${API_URL}/desk/height`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ height: currentHeight })
    });
}

async function saveCurrentAsPreset() {
    const name = document.getElementById('new-preset-name').value;
    if (!name) return alert("Enter a name");
    
    await fetch(`${API_URL}/presets/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, height: currentHeight })
    });
    
    document.getElementById('new-preset-name').value = '';
    fetchPresets();
}
