"""HTML generation for timeline preview interface."""


class HTMLGeneratorMixin:
    """Mixin for generating timeline preview HTML."""

    def _generate_default_html(self) -> str:
        """Generate default HTML for timeline preview."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alice Timeline Preview</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #1a1a1a;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1 {
            color: #fff;
            margin-bottom: 30px;
        }
        
        .preview-container {
            background: #2a2a2a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .video-preview {
            width: 100%;
            max-width: 800px;
            aspect-ratio: 16/9;
            background: #000;
            margin: 0 auto 20px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: #666;
        }
        
        .timeline-container {
            background: #222;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
            overflow-x: auto;
        }
        
        .timeline-track {
            display: flex;
            gap: 2px;
            min-height: 80px;
            padding: 10px 0;
        }
        
        .timeline-clip {
            background: #4a7c59;
            border-radius: 4px;
            padding: 10px;
            min-width: 100px;
            cursor: move;
            transition: transform 0.2s;
            color: white;
            text-align: center;
        }
        
        .timeline-clip:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .timeline-clip.dragging {
            opacity: 0.5;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        button {
            background: #4a7c59;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        
        button:hover {
            background: #5a8d69;
        }
        
        button:disabled {
            background: #333;
            color: #666;
            cursor: not-allowed;
        }
        
        .status {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #333;
            padding: 15px 20px;
            border-radius: 4px;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s;
        }
        
        .status.show {
            opacity: 1;
            transform: translateY(0);
        }
        
        .status.success {
            background: #4a7c59;
        }
        
        .status.error {
            background: #c44;
        }
        
        .status.info {
            background: #448;
        }
        
        /* Keyboard shortcuts help */
        .shortcuts {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: #2a2a2a;
            padding: 15px;
            border-radius: 4px;
            font-size: 12px;
            opacity: 0.7;
        }
        
        .shortcuts h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
        }
        
        .shortcuts dl {
            margin: 0;
        }
        
        .shortcuts dt {
            display: inline-block;
            width: 60px;
            font-weight: bold;
            color: #4a7c59;
        }
        
        .shortcuts dd {
            display: inline;
            margin: 0 0 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Timeline Preview</h1>
        
        <div class="preview-container">
            <div class="video-preview" id="video-preview">
                Preview Area
            </div>
            
            <div class="timeline-container">
                <div class="timeline-track" id="timeline-track">
                    <!-- Timeline clips will be rendered here -->
                </div>
            </div>
            
            <div class="controls">
                <button onclick="playPreview()">Play</button>
                <button onclick="pausePreview()">Pause</button>
                <button onclick="undoChange()" id="undo-btn">Undo</button>
                <button onclick="redoChange()" id="redo-btn">Redo</button>
                <button onclick="exportTimeline('edl')">Export EDL</button>
                <button onclick="exportTimeline('xml')">Export XML</button>
                <button onclick="exportTimeline('json')">Export JSON</button>
            </div>
        </div>
        
        <div class="shortcuts">
            <h3>Keyboard Shortcuts</h3>
            <dl>
                <dt>Space</dt><dd>Play/Pause</dd><br>
                <dt>Ctrl+Z</dt><dd>Undo</dd><br>
                <dt>Ctrl+Y</dt><dd>Redo</dd><br>
                <dt>Delete</dt><dd>Remove selected clip</dd><br>
                <dt>Ctrl+D</dt><dd>Duplicate selected clip</dd>
            </dl>
        </div>
        
        <div class="status" id="status"></div>
    </div>
    
    <script>
        let sessionId = null;
        let timeline = null;
        let ws = null;
        let selectedClipIndex = null;
        
        // Initialize
        async function init() {
            // Check if we have a session ID in URL
            const urlParams = new URLSearchParams(window.location.search);
            sessionId = urlParams.get('session');
            
            if (sessionId) {
                await loadSession(sessionId);
            } else {
                showStatus('No session ID provided', 'error');
            }
            
            // Set up keyboard shortcuts
            setupKeyboardShortcuts();
        }
        
        async function loadSession(id) {
            try {
                const response = await fetch(`/session/${id}`);
                const data = await response.json();
                
                if (response.ok) {
                    timeline = data.timeline;
                    renderTimeline();
                    updateControls(data.can_undo, data.can_redo);
                    connectWebSocket(id);
                } else {
                    showStatus('Failed to load session', 'error');
                }
            } catch (error) {
                console.error('Error loading session:', error);
                showStatus('Error loading session', 'error');
            }
        }
        
        function renderTimeline() {
            const track = document.getElementById('timeline-track');
            track.innerHTML = '';
            
            if (!timeline || !timeline.clips) return;
            
            timeline.clips.forEach((clip, index) => {
                const clipEl = document.createElement('div');
                clipEl.className = 'timeline-clip';
                clipEl.draggable = true;
                clipEl.dataset.index = index;
                clipEl.innerHTML = `
                    <div style="font-size: 12px; font-weight: bold;">Clip ${index + 1}</div>
                    <div style="font-size: 10px; opacity: 0.8;">${clip.duration.toFixed(1)}s</div>
                `;
                
                // Add drag handlers
                clipEl.addEventListener('dragstart', handleDragStart);
                clipEl.addEventListener('dragover', handleDragOver);
                clipEl.addEventListener('drop', handleDrop);
                clipEl.addEventListener('dragend', handleDragEnd);
                
                // Add click handler for selection
                clipEl.addEventListener('click', () => selectClip(index));
                
                track.appendChild(clipEl);
            });
        }
        
        function selectClip(index) {
            selectedClipIndex = index;
            // Update visual selection
            document.querySelectorAll('.timeline-clip').forEach((el, i) => {
                el.style.outline = i === index ? '2px solid #4a7c59' : 'none';
            });
        }
        
        function connectWebSocket(id) {
            ws = new WebSocket(`ws://localhost:8001/ws/${id}`);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
                ws.send(JSON.stringify({ type: 'get_timeline' }));
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'timeline_update') {
                    timeline = data.timeline;
                    renderTimeline();
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                showStatus('Connection error', 'error');
            };
        }
        
        // Drag and drop handlers
        let draggedElement = null;
        
        function handleDragStart(e) {
            draggedElement = e.target;
            e.target.style.opacity = '0.5';
        }
        
        function handleDragOver(e) {
            if (e.preventDefault) {
                e.preventDefault();
            }
            e.dataTransfer.dropEffect = 'move';
            return false;
        }
        
        function handleDrop(e) {
            if (e.stopPropagation) {
                e.stopPropagation();
            }
            
            if (draggedElement !== e.target) {
                const oldIndex = parseInt(draggedElement.dataset.index);
                const newIndex = parseInt(e.target.dataset.index);
                
                reorderClips(oldIndex, newIndex);
            }
            
            return false;
        }
        
        function handleDragEnd(e) {
            e.target.style.opacity = '';
        }
        
        // Timeline operations
        async function reorderClips(oldIndex, newIndex) {
            try {
                const response = await fetch(`/session/${sessionId}/update`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        timeline_id: sessionId,
                        operation: 'reorder',
                        clips: [{ old_index: oldIndex, new_index: newIndex }]
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    timeline = data.timeline;
                    renderTimeline();
                    showStatus('Timeline updated', 'success');
                }
            } catch (error) {
                console.error('Error reordering clips:', error);
                showStatus('Failed to reorder clips', 'error');
            }
        }
        
        async function undoChange() {
            try {
                const response = await fetch(`/session/${sessionId}/undo`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                if (data.success) {
                    timeline = data.timeline;
                    renderTimeline();
                    showStatus('Undone', 'success');
                }
            } catch (error) {
                console.error('Error undoing:', error);
                showStatus('Failed to undo', 'error');
            }
        }
        
        async function redoChange() {
            try {
                const response = await fetch(`/session/${sessionId}/redo`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                if (data.success) {
                    timeline = data.timeline;
                    renderTimeline();
                    showStatus('Redone', 'success');
                }
            } catch (error) {
                console.error('Error redoing:', error);
                showStatus('Failed to redo', 'error');
            }
        }
        
        async function exportTimeline(format) {
            try {
                const response = await fetch(`/session/${sessionId}/export?format=${format}`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                // Create download link
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `timeline.${format}`;
                a.click();
                URL.revokeObjectURL(url);
                
                showStatus(`Exported as ${format.toUpperCase()}`, 'success');
            } catch (error) {
                console.error('Error exporting:', error);
                showStatus('Failed to export', 'error');
            }
        }
        
        function playPreview() {
            showStatus('Playback not yet implemented', 'info');
        }
        
        function pausePreview() {
            showStatus('Playback not yet implemented', 'info');
        }
        
        function updateControls(canUndo, canRedo) {
            document.getElementById('undo-btn').disabled = !canUndo;
            document.getElementById('redo-btn').disabled = !canRedo;
        }
        
        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status show ${type}`;
            
            setTimeout(() => {
                status.classList.remove('show');
            }, 3000);
        }
        
        // Keyboard shortcuts
        function setupKeyboardShortcuts() {
            document.addEventListener('keydown', async (e) => {
                // Space: Play/Pause
                if (e.code === 'Space' && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    playPreview();
                }
                
                // Ctrl+Z: Undo
                if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
                    e.preventDefault();
                    await undoChange();
                }
                
                // Ctrl+Y: Redo
                if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
                    e.preventDefault();
                    await redoChange();
                }
                
                // Delete: Remove selected clip
                if (e.key === 'Delete' && selectedClipIndex !== null) {
                    e.preventDefault();
                    await removeClip(selectedClipIndex);
                }
                
                // Ctrl+D: Duplicate selected clip
                if ((e.ctrlKey || e.metaKey) && e.key === 'd' && selectedClipIndex !== null) {
                    e.preventDefault();
                    await duplicateClip(selectedClipIndex);
                }
            });
        }
        
        async function removeClip(index) {
            try {
                const response = await fetch(`/session/${sessionId}/update`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        timeline_id: sessionId,
                        operation: 'remove_clip',
                        clips: [{ index: index }]
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    timeline = data.timeline;
                    renderTimeline();
                    selectedClipIndex = null;
                    showStatus('Clip removed', 'success');
                }
            } catch (error) {
                console.error('Error removing clip:', error);
                showStatus('Failed to remove clip', 'error');
            }
        }
        
        async function duplicateClip(index) {
            try {
                const response = await fetch(`/session/${sessionId}/update`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        timeline_id: sessionId,
                        operation: 'duplicate_clip',
                        clips: [{ index: index }]
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    timeline = data.timeline;
                    renderTimeline();
                    showStatus('Clip duplicated', 'success');
                }
            } catch (error) {
                console.error('Error duplicating clip:', error);
                showStatus('Failed to duplicate clip', 'error');
            }
        }
        
        // Initialize on load
        window.addEventListener('load', init);
    </script>
</body>
</html>
        """
