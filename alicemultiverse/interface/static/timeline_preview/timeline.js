/**
 * Timeline Preview Interface
 * Main JavaScript for timeline manipulation and WebSocket communication
 */

class TimelineManager {
    constructor() {
        this.ws = null;
        this.sessionId = null;
        this.timeline = null;
        this.selectedClip = null;
        this.videoPlayer = null;
        
        // Drag state
        this.isDragging = false;
        this.draggedClip = null;
        this.dragOffset = 0;
        
        // Initialize
        this.init();
    }
    
    async init() {
        // Get session ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        this.sessionId = urlParams.get('session');
        
        if (!this.sessionId) {
            this.showError('No session ID provided');
            return;
        }
        
        // Connect to WebSocket
        this.connectWebSocket();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load timeline
        await this.loadTimeline();
    }
    
    connectWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws/${this.sessionId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            // Attempt reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showError('Connection error');
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'timeline_update':
                this.timeline = data.timeline;
                this.renderTimeline();
                if (this.videoPlayer) {
                    this.videoPlayer.updateTimeline(this.timeline);
                }
                break;
            case 'export_complete':
                this.showStatus(`Export complete: ${data.filename}`);
                break;
            case 'error':
                this.showError(data.message);
                break;
        }
    }
    
    async loadTimeline() {
        try {
            const response = await fetch(`/api/timeline/${this.sessionId}`);
            if (!response.ok) throw new Error('Failed to load timeline');
            
            const data = await response.json();
            this.timeline = data.timeline;
            
            // Initialize video player
            const videoElement = document.getElementById('preview-video');
            const canvasElement = document.getElementById('preview-canvas');
            
            // Use canvas for custom rendering
            videoElement.style.display = 'none';
            canvasElement.style.display = 'block';
            document.getElementById('preview-placeholder').style.display = 'none';
            
            this.videoPlayer = new VideoPlayer(videoElement, canvasElement, this.timeline);
            
            // Render timeline
            this.renderTimeline();
            
            // Extract and set thumbnails
            this.loadThumbnails();
            
        } catch (error) {
            console.error('Error loading timeline:', error);
            this.showError('Failed to load timeline');
        }
    }
    
    async loadThumbnails() {
        if (!this.videoPlayer) return;
        
        try {
            const thumbnails = await this.videoPlayer.extractThumbnails();
            
            // Update clip elements with thumbnails
            for (const [clipId, dataUrl] of thumbnails.entries()) {
                const clipElement = document.querySelector(`[data-clip-id="${clipId}"]`);
                if (clipElement) {
                    const img = clipElement.querySelector('.clip-thumbnail');
                    if (img) {
                        img.src = dataUrl;
                    }
                }
            }
        } catch (error) {
            console.error('Error loading thumbnails:', error);
        }
    }
    
    renderTimeline() {
        const track = document.getElementById('timeline-track');
        const ruler = document.getElementById('timeline-ruler');
        const beatMarkers = document.getElementById('beat-markers');
        
        // Clear existing content
        track.innerHTML = '';
        ruler.innerHTML = '';
        beatMarkers.innerHTML = '';
        
        if (!this.timeline) return;
        
        // Calculate pixels per second
        const timelineWidth = track.offsetWidth;
        const pixelsPerSecond = timelineWidth / this.timeline.duration;
        
        // Render time markers
        this.renderTimeMarkers(ruler, pixelsPerSecond);
        
        // Render clips
        this.timeline.clips.forEach((clip, index) => {
            const clipElement = this.createClipElement(clip, index, pixelsPerSecond);
            track.appendChild(clipElement);
        });
        
        // Render beat markers if available
        if (this.timeline.markers) {
            this.renderBeatMarkers(beatMarkers, pixelsPerSecond);
        }
    }
    
    renderTimeMarkers(ruler, pixelsPerSecond) {
        const duration = this.timeline.duration;
        const interval = this.getTimeInterval(duration);
        
        for (let time = 0; time <= duration; time += interval) {
            const marker = document.createElement('div');
            marker.className = 'time-marker';
            marker.style.left = `${time * pixelsPerSecond}px`;
            marker.textContent = this.formatTime(time);
            ruler.appendChild(marker);
        }
    }
    
    getTimeInterval(duration) {
        if (duration <= 30) return 5;
        if (duration <= 60) return 10;
        if (duration <= 300) return 30;
        return 60;
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        if (mins === 0) return `${secs}s`;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    createClipElement(clip, index, pixelsPerSecond) {
        const clipDiv = document.createElement('div');
        clipDiv.className = 'timeline-clip';
        clipDiv.dataset.clipIndex = index;
        clipDiv.dataset.clipId = clip.id || clip.path;
        
        // Position and size
        clipDiv.style.left = `${clip.start_time * pixelsPerSecond}px`;
        clipDiv.style.width = `${clip.duration * pixelsPerSecond}px`;
        
        // Thumbnail
        const thumbnail = document.createElement('img');
        thumbnail.className = 'clip-thumbnail';
        thumbnail.src = '/static/placeholder.jpg'; // Default placeholder
        clipDiv.appendChild(thumbnail);
        
        // Clip info
        const info = document.createElement('div');
        info.className = 'clip-info';
        
        const name = document.createElement('div');
        name.className = 'clip-name';
        name.textContent = clip.path.split('/').pop();
        
        const duration = document.createElement('div');
        duration.className = 'clip-duration';
        duration.textContent = `${clip.duration.toFixed(1)}s`;
        
        info.appendChild(name);
        info.appendChild(duration);
        clipDiv.appendChild(info);
        
        // Transitions
        if (clip.transition_in) {
            const transIn = document.createElement('div');
            transIn.className = 'clip-transition in';
            clipDiv.appendChild(transIn);
        }
        
        if (clip.transition_out) {
            const transOut = document.createElement('div');
            transOut.className = 'clip-transition out';
            clipDiv.appendChild(transOut);
        }
        
        // Event listeners
        clipDiv.addEventListener('mousedown', (e) => this.startDrag(e, index));
        clipDiv.addEventListener('click', (e) => this.selectClip(e, index));
        clipDiv.addEventListener('dblclick', (e) => this.editClip(e, index));
        
        return clipDiv;
    }
    
    renderBeatMarkers(container, pixelsPerSecond) {
        this.timeline.markers
            .filter(marker => marker.type === 'beat')
            .forEach(marker => {
                const markerDiv = document.createElement('div');
                markerDiv.className = 'beat-marker';
                if (marker.strong) markerDiv.classList.add('strong');
                markerDiv.style.left = `${marker.time * pixelsPerSecond}px`;
                container.appendChild(markerDiv);
            });
    }
    
    setupEventListeners() {
        // Drag and drop
        document.addEventListener('mousemove', (e) => this.onDrag(e));
        document.addEventListener('mouseup', (e) => this.endDrag(e));
        
        // Undo/Redo
        document.getElementById('undo-btn').addEventListener('click', () => this.undo());
        document.getElementById('redo-btn').addEventListener('click', () => this.redo());
        
        // Export
        document.getElementById('export-btn').addEventListener('click', () => this.showExportDialog());
        document.getElementById('export-confirm').addEventListener('click', () => this.exportTimeline());
        document.getElementById('export-cancel').addEventListener('click', () => this.hideExportDialog());
        
        // Inspector
        document.getElementById('apply-changes').addEventListener('click', () => this.applyClipChanges());
    }
    
    startDrag(event, clipIndex) {
        if (event.button !== 0) return; // Left click only
        
        this.isDragging = true;
        this.draggedClip = clipIndex;
        
        const clipElement = event.currentTarget;
        clipElement.classList.add('dragging');
        
        // Calculate offset from mouse to clip start
        const rect = clipElement.getBoundingClientRect();
        this.dragOffset = event.clientX - rect.left;
        
        event.preventDefault();
    }
    
    onDrag(event) {
        if (!this.isDragging || this.draggedClip === null) return;
        
        const track = document.getElementById('timeline-track');
        const trackRect = track.getBoundingClientRect();
        const pixelsPerSecond = track.offsetWidth / this.timeline.duration;
        
        // Calculate new position
        const x = event.clientX - trackRect.left - this.dragOffset;
        const newStartTime = Math.max(0, x / pixelsPerSecond);
        
        // Update clip element position
        const clipElement = track.children[this.draggedClip];
        clipElement.style.left = `${newStartTime * pixelsPerSecond}px`;
    }
    
    endDrag(event) {
        if (!this.isDragging || this.draggedClip === null) return;
        
        this.isDragging = false;
        
        const track = document.getElementById('timeline-track');
        const trackRect = track.getBoundingClientRect();
        const pixelsPerSecond = track.offsetWidth / this.timeline.duration;
        
        // Calculate final position
        const x = event.clientX - trackRect.left - this.dragOffset;
        const newStartTime = Math.max(0, x / pixelsPerSecond);
        
        // Remove dragging class
        const clipElement = track.children[this.draggedClip];
        clipElement.classList.remove('dragging');
        
        // Update timeline
        const updatedClips = [...this.timeline.clips];
        updatedClips[this.draggedClip].start_time = newStartTime;
        
        // Reorder clips by start time
        updatedClips.sort((a, b) => a.start_time - b.start_time);
        
        // Send update
        this.updateTimeline({ clips: updatedClips });
        
        this.draggedClip = null;
    }
    
    selectClip(event, clipIndex) {
        // Remove previous selection
        document.querySelectorAll('.timeline-clip.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Select new clip
        const clipElement = event.currentTarget;
        clipElement.classList.add('selected');
        this.selectedClip = clipIndex;
        
        // Show inspector
        this.showClipInspector(this.timeline.clips[clipIndex]);
    }
    
    editClip(event, clipIndex) {
        this.selectClip(event, clipIndex);
        // Focus on duration input
        document.getElementById('clip-duration').focus();
    }
    
    showClipInspector(clip) {
        const inspector = document.getElementById('clip-inspector');
        inspector.style.display = 'block';
        
        // Populate fields
        document.getElementById('clip-duration').value = clip.duration.toFixed(1);
        document.getElementById('clip-transition').value = clip.transition_in || '';
        document.getElementById('transition-duration').value = clip.transition_in_duration || 0.5;
    }
    
    applyClipChanges() {
        if (this.selectedClip === null) return;
        
        const clip = this.timeline.clips[this.selectedClip];
        const updatedClips = [...this.timeline.clips];
        
        // Update clip properties
        updatedClips[this.selectedClip] = {
            ...clip,
            duration: parseFloat(document.getElementById('clip-duration').value),
            transition_in: document.getElementById('clip-transition').value || null,
            transition_in_duration: parseFloat(document.getElementById('transition-duration').value)
        };
        
        // Send update
        this.updateTimeline({ clips: updatedClips });
    }
    
    updateTimeline(updates) {
        const message = {
            type: 'update_timeline',
            timeline_id: this.sessionId,
            updates: updates
        };
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    undo() {
        const message = {
            type: 'undo',
            timeline_id: this.sessionId
        };
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    redo() {
        const message = {
            type: 'redo',
            timeline_id: this.sessionId
        };
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    showExportDialog() {
        document.getElementById('export-dialog').style.display = 'flex';
    }
    
    hideExportDialog() {
        document.getElementById('export-dialog').style.display = 'none';
    }
    
    async exportTimeline() {
        const format = document.getElementById('export-format').value;
        
        try {
            const response = await fetch(`/api/timeline/${this.sessionId}/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format })
            });
            
            if (!response.ok) throw new Error('Export failed');
            
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            // Download file
            const a = document.createElement('a');
            a.href = url;
            a.download = `timeline_${this.sessionId}.${format}`;
            a.click();
            
            URL.revokeObjectURL(url);
            this.hideExportDialog();
            this.showStatus('Export complete');
            
        } catch (error) {
            console.error('Export error:', error);
            this.showError('Export failed');
        }
    }
    
    updateConnectionStatus(connected) {
        const status = document.getElementById('connection-status');
        if (connected) {
            status.classList.add('connected');
            status.classList.remove('disconnected');
            status.textContent = 'Connected';
        } else {
            status.classList.remove('connected');
            status.classList.add('disconnected');
            status.textContent = 'Disconnected';
        }
    }
    
    showStatus(message) {
        const status = document.getElementById('status');
        status.textContent = message;
        status.style.color = '#00cc44';
        setTimeout(() => {
            status.textContent = 'Ready';
            status.style.color = '';
        }, 3000);
    }
    
    showError(message) {
        const status = document.getElementById('status');
        status.textContent = `Error: ${message}`;
        status.style.color = '#cc0000';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TimelineManager();
});