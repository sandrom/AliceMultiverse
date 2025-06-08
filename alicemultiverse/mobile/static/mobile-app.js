/**
 * Alice Mobile Companion - Client-side JavaScript
 */

let ws = null;
let token = null;
let currentTimeline = null;
let draggedElement = null;
let touchStartY = 0;
let originalIndex = 0;

// Authentication
async function authenticate() {
    const tokenInput = document.getElementById('tokenInput');
    token = tokenInput.value.trim();
    
    if (!token) {
        alert('Please enter your access token');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/validate', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('alice_token', token);
            showMainScreen();
            connectWebSocket();
            loadTimelines();
        } else {
            alert('Invalid token');
        }
    } catch (error) {
        alert('Connection error: ' + error.message);
    }
}

// WebSocket connection
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        updateConnectionStatus(true);
        
        // Authenticate WebSocket
        ws.send(JSON.stringify({
            type: 'auth',
            token: token
        }));
        
        // Keep alive
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
        
        // Attempt to reconnect
        setTimeout(connectWebSocket, 3000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'timeline_update':
            if (currentTimeline && currentTimeline.id === message.timeline_id) {
                updateClipsList(message.timeline);
            }
            break;
        case 'pong':
            // Keep alive response
            break;
        case 'error':
            alert(message.message);
            break;
    }
}

// UI Functions
function showMainScreen() {
    document.getElementById('authScreen').style.display = 'none';
    document.getElementById('mainScreen').style.display = 'block';
}

function updateConnectionStatus(connected) {
    const status = document.getElementById('connectionStatus');
    if (connected) {
        status.textContent = 'Connected';
        status.className = 'status connected';
    } else {
        status.textContent = 'Disconnected';
        status.className = 'status disconnected';
    }
}

async function loadTimelines() {
    try {
        const response = await fetch('/api/timelines', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayTimelines(data.timelines);
        }
    } catch (error) {
        console.error('Error loading timelines:', error);
    }
}

function displayTimelines(timelines) {
    const container = document.getElementById('timelineList');
    container.innerHTML = '';
    
    if (timelines.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">No timelines available</p>';
        return;
    }
    
    timelines.forEach(timeline => {
        const item = document.createElement('div');
        item.className = 'timeline-item';
        item.onclick = () => loadTimeline(timeline.id);
        
        item.innerHTML = `
            <h3>${timeline.name}</h3>
            <div class="info">
                ${timeline.clip_count} clips • ${formatDuration(timeline.duration)}
            </div>
        `;
        
        container.appendChild(item);
    });
}

async function loadTimeline(timelineId) {
    try {
        const response = await fetch(`/api/timeline/${timelineId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const timeline = await response.json();
            currentTimeline = timeline;
            showTimelineView(timeline);
        }
    } catch (error) {
        console.error('Error loading timeline:', error);
    }
}

function showTimelineView(timeline) {
    document.getElementById('timelineList').style.display = 'none';
    document.getElementById('clipsContainer').style.display = 'block';
    document.getElementById('timelineName').textContent = timeline.name;
    
    updateClipsList(timeline);
}

function updateClipsList(timeline) {
    const container = document.getElementById('clipsList');
    container.innerHTML = '';
    
    timeline.clips.forEach((clip, index) => {
        const clipElement = createClipElement(clip, index);
        container.appendChild(clipElement);
    });
}

function createClipElement(clip, index) {
    const div = document.createElement('div');
    div.className = 'clip';
    div.dataset.clipId = clip.id;
    div.dataset.index = index;
    
    div.innerHTML = `
        <img src="${clip.thumbnail}" class="clip-thumbnail" loading="lazy">
        <div class="clip-info">
            <h4>Clip ${index + 1}</h4>
            <div class="duration">${formatDuration(clip.duration)}</div>
        </div>
        <div class="drag-handle">☰</div>
    `;
    
    // Touch events for drag and drop
    div.addEventListener('touchstart', handleTouchStart, { passive: false });
    div.addEventListener('touchmove', handleTouchMove, { passive: false });
    div.addEventListener('touchend', handleTouchEnd);
    
    // Mouse events for desktop testing
    div.addEventListener('mousedown', handleMouseDown);
    
    return div;
}

// Drag and Drop
function handleTouchStart(e) {
    e.preventDefault();
    const touch = e.touches[0];
    startDrag(e.target.closest('.clip'), touch.clientY);
}

function handleMouseDown(e) {
    e.preventDefault();
    startDrag(e.target.closest('.clip'), e.clientY);
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
}

function startDrag(element, clientY) {
    if (!element) return;
    
    draggedElement = element;
    touchStartY = clientY;
    originalIndex = parseInt(element.dataset.index);
    
    element.classList.add('dragging');
    element.style.position = 'relative';
    element.style.zIndex = '1000';
}

function handleTouchMove(e) {
    e.preventDefault();
    if (!draggedElement) return;
    
    const touch = e.touches[0];
    moveElement(touch.clientY);
}

function handleMouseMove(e) {
    if (!draggedElement) return;
    moveElement(e.clientY);
}

function moveElement(clientY) {
    const deltaY = clientY - touchStartY;
    draggedElement.style.transform = `translateY(${deltaY}px)`;
    
    // Check for swap
    const clips = Array.from(document.querySelectorAll('.clip'));
    const draggedRect = draggedElement.getBoundingClientRect();
    const draggedMidY = draggedRect.top + draggedRect.height / 2;
    
    clips.forEach((clip, index) => {
        if (clip === draggedElement) return;
        
        const rect = clip.getBoundingClientRect();
        const midY = rect.top + rect.height / 2;
        
        if (draggedMidY > rect.top && draggedMidY < rect.bottom) {
            const draggedIndex = parseInt(draggedElement.dataset.index);
            
            if (draggedIndex < index && draggedMidY > midY) {
                // Moving down
                swapClips(draggedIndex, index);
            } else if (draggedIndex > index && draggedMidY < midY) {
                // Moving up
                swapClips(draggedIndex, index);
            }
        }
    });
}

function handleTouchEnd(e) {
    e.preventDefault();
    endDrag();
}

function handleMouseUp(e) {
    endDrag();
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
}

function endDrag() {
    if (!draggedElement) return;
    
    draggedElement.classList.remove('dragging');
    draggedElement.style.position = '';
    draggedElement.style.transform = '';
    draggedElement.style.zIndex = '';
    
    draggedElement = null;
}

function swapClips(index1, index2) {
    const clips = Array.from(document.querySelectorAll('.clip'));
    const clip1 = clips[index1];
    const clip2 = clips[index2];
    
    // Update data attributes
    clip1.dataset.index = index2;
    clip2.dataset.index = index1;
    
    // Swap in DOM
    const parent = clip1.parentNode;
    const temp = document.createElement('div');
    parent.insertBefore(temp, clip1);
    parent.insertBefore(clip1, clip2);
    parent.insertBefore(clip2, temp);
    parent.removeChild(temp);
}

async function saveOrder() {
    const clips = Array.from(document.querySelectorAll('.clip'));
    const clipIds = clips.map(clip => clip.dataset.clipId);
    
    try {
        const response = await fetch(`/api/timeline/${currentTimeline.id}/reorder`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(clipIds)
        });
        
        if (response.ok) {
            showToast('Timeline saved!');
        } else {
            showToast('Failed to save timeline');
        }
    } catch (error) {
        console.error('Error saving timeline:', error);
        showToast('Connection error');
    }
}

function showTimelines() {
    document.getElementById('clipsContainer').style.display = 'none';
    document.getElementById('timelineList').style.display = 'block';
    currentTimeline = null;
    loadTimelines();
}

// Utilities
function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function showToast(message) {
    // Simple toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 15px 30px;
        border-radius: 30px;
        z-index: 2000;
        animation: slideUp 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideDown 0.3s ease';
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 2000);
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { transform: translate(-50%, 100px); opacity: 0; }
        to { transform: translate(-50%, 0); opacity: 1; }
    }
    @keyframes slideDown {
        from { transform: translate(-50%, 0); opacity: 1; }
        to { transform: translate(-50%, 100px); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Check for saved token on load
window.addEventListener('load', () => {
    const savedToken = localStorage.getItem('alice_token');
    if (savedToken) {
        document.getElementById('tokenInput').value = savedToken;
    }
});