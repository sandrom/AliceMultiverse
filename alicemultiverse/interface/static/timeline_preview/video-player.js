/**
 * Video Player Module for Timeline Preview
 * Handles video playback, frame extraction, and synchronization
 */

class VideoPlayer {
    constructor(videoElement, canvasElement, timeline) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.ctx = canvasElement.getContext('2d');
        this.timeline = timeline;
        
        this.isPlaying = false;
        this.currentTime = 0;
        this.duration = 0;
        
        // Playback state
        this.playbackRate = 1.0;
        this.loop = false;
        
        // Frame cache for smooth scrubbing
        this.frameCache = new Map();
        this.cacheSize = 100; // Maximum cached frames
        
        // Clip video sources
        this.clipVideos = new Map(); // clipId -> video element
        
        // Initialize
        this.init();
    }
    
    async init() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Load clip videos
        await this.loadClipVideos();
        
        // Calculate total duration
        this.calculateDuration();
    }
    
    setupEventListeners() {
        // Playback controls
        document.getElementById('play-btn').addEventListener('click', () => this.togglePlayback());
        document.getElementById('stop-btn').addEventListener('click', () => this.stop());
        
        // Timeline interaction
        const ruler = document.getElementById('timeline-ruler');
        ruler.addEventListener('click', (e) => this.seekToPosition(e));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }
    
    async loadClipVideos() {
        // Create video elements for each unique clip
        const uniquePaths = new Set(this.timeline.clips.map(clip => clip.path));
        
        for (const path of uniquePaths) {
            const video = document.createElement('video');
            video.src = `/media/${path}`; // Assuming media endpoint
            video.preload = 'metadata';
            video.crossOrigin = 'anonymous';
            
            await new Promise((resolve, reject) => {
                video.addEventListener('loadedmetadata', resolve);
                video.addEventListener('error', reject);
                video.load();
            });
            
            this.clipVideos.set(path, video);
        }
    }
    
    calculateDuration() {
        // Calculate total timeline duration
        if (this.timeline.clips.length > 0) {
            const lastClip = this.timeline.clips[this.timeline.clips.length - 1];
            this.duration = lastClip.start_time + lastClip.duration;
        }
        
        // Update time display
        this.updateTimeDisplay();
    }
    
    togglePlayback() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    async play() {
        this.isPlaying = true;
        document.getElementById('play-btn').textContent = '⏸️';
        
        // Start playback loop
        this.lastFrameTime = performance.now();
        this.playbackLoop();
    }
    
    pause() {
        this.isPlaying = false;
        document.getElementById('play-btn').textContent = '▶️';
    }
    
    stop() {
        this.pause();
        this.currentTime = 0;
        this.updatePlayhead();
        this.renderFrame();
    }
    
    playbackLoop() {
        if (!this.isPlaying) return;
        
        const now = performance.now();
        const deltaTime = (now - this.lastFrameTime) / 1000; // Convert to seconds
        this.lastFrameTime = now;
        
        // Update current time
        this.currentTime += deltaTime * this.playbackRate;
        
        // Check if we've reached the end
        if (this.currentTime >= this.duration) {
            if (this.loop) {
                this.currentTime = 0;
            } else {
                this.stop();
                return;
            }
        }
        
        // Update visuals
        this.updatePlayhead();
        this.renderFrame();
        
        // Continue loop
        requestAnimationFrame(() => this.playbackLoop());
    }
    
    async renderFrame() {
        // Find current clip
        const currentClip = this.timeline.clips.find(clip => 
            this.currentTime >= clip.start_time && 
            this.currentTime < clip.start_time + clip.duration
        );
        
        if (!currentClip) {
            // Clear canvas if no clip
            this.ctx.fillStyle = '#000';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            return;
        }
        
        // Get video element for this clip
        const video = this.clipVideos.get(currentClip.path);
        if (!video) return;
        
        // Calculate clip-relative time
        const clipTime = this.currentTime - currentClip.start_time;
        
        // Check frame cache
        const cacheKey = `${currentClip.path}_${Math.floor(clipTime * 30)}`; // 30fps cache
        if (this.frameCache.has(cacheKey)) {
            const cachedFrame = this.frameCache.get(cacheKey);
            this.ctx.putImageData(cachedFrame, 0, 0);
            return;
        }
        
        // Seek video to correct time
        if (Math.abs(video.currentTime - clipTime) > 0.1) {
            video.currentTime = clipTime;
            await new Promise(resolve => {
                video.addEventListener('seeked', resolve, { once: true });
            });
        }
        
        // Draw current frame
        this.drawFrame(video, currentClip);
        
        // Apply transitions if needed
        this.applyTransitions(currentClip, clipTime);
        
        // Cache frame
        this.cacheFrame(cacheKey);
    }
    
    drawFrame(video, clip) {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Calculate aspect ratio preserving scale
        const videoAspect = video.videoWidth / video.videoHeight;
        const canvasAspect = this.canvas.width / this.canvas.height;
        
        let drawWidth, drawHeight, offsetX, offsetY;
        
        if (videoAspect > canvasAspect) {
            // Video is wider
            drawWidth = this.canvas.width;
            drawHeight = this.canvas.width / videoAspect;
            offsetX = 0;
            offsetY = (this.canvas.height - drawHeight) / 2;
        } else {
            // Video is taller
            drawHeight = this.canvas.height;
            drawWidth = this.canvas.height * videoAspect;
            offsetX = (this.canvas.width - drawWidth) / 2;
            offsetY = 0;
        }
        
        // Draw video frame
        this.ctx.drawImage(video, offsetX, offsetY, drawWidth, drawHeight);
    }
    
    applyTransitions(clip, clipTime) {
        const clipDuration = clip.duration;
        
        // Fade in transition
        if (clip.transition_in && clipTime < clip.transition_in_duration) {
            const opacity = clipTime / clip.transition_in_duration;
            this.applyFade(1 - opacity);
        }
        
        // Fade out transition
        if (clip.transition_out && clipTime > clipDuration - clip.transition_out_duration) {
            const fadeTime = clipTime - (clipDuration - clip.transition_out_duration);
            const opacity = fadeTime / clip.transition_out_duration;
            this.applyFade(opacity);
        }
    }
    
    applyFade(opacity) {
        // Apply fade by drawing black overlay
        this.ctx.fillStyle = `rgba(0, 0, 0, ${opacity})`;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    cacheFrame(key) {
        // Cache current canvas content
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        this.frameCache.set(key, imageData);
        
        // Maintain cache size
        if (this.frameCache.size > this.cacheSize) {
            const firstKey = this.frameCache.keys().next().value;
            this.frameCache.delete(firstKey);
        }
    }
    
    seekToPosition(event) {
        const rect = event.currentTarget.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const percentage = x / rect.width;
        
        this.currentTime = percentage * this.duration;
        this.updatePlayhead();
        this.renderFrame();
    }
    
    updatePlayhead() {
        const playhead = document.getElementById('playhead');
        const percentage = this.currentTime / this.duration;
        const timelineWidth = document.getElementById('timeline-track').offsetWidth;
        
        playhead.style.left = `${percentage * timelineWidth}px`;
        
        this.updateTimeDisplay();
    }
    
    updateTimeDisplay() {
        const display = document.getElementById('time-display');
        const current = this.formatTime(this.currentTime);
        const total = this.formatTime(this.duration);
        display.textContent = `${current} / ${total}`;
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    handleKeyboard(event) {
        switch(event.key) {
            case ' ':
                event.preventDefault();
                this.togglePlayback();
                break;
            case 'ArrowLeft':
                event.preventDefault();
                this.seek(-1);
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.seek(1);
                break;
            case 'Home':
                event.preventDefault();
                this.currentTime = 0;
                this.updatePlayhead();
                this.renderFrame();
                break;
            case 'End':
                event.preventDefault();
                this.currentTime = this.duration;
                this.updatePlayhead();
                this.renderFrame();
                break;
        }
    }
    
    seek(seconds) {
        this.currentTime = Math.max(0, Math.min(this.duration, this.currentTime + seconds));
        this.updatePlayhead();
        this.renderFrame();
    }
    
    // Generate preview video file
    async generatePreview() {
        // This would typically be handled server-side
        // Here we can prepare the request
        const previewData = {
            timeline: this.timeline,
            format: 'mp4',
            resolution: [this.canvas.width, this.canvas.height],
            includeAudio: true
        };
        
        // Send to server
        const response = await fetch('/api/preview/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(previewData)
        });
        
        if (response.ok) {
            const result = await response.json();
            return result.preview_url;
        }
        
        throw new Error('Failed to generate preview');
    }
    
    // Extract frames for timeline thumbnails
    async extractThumbnails() {
        const thumbnails = new Map();
        
        for (const clip of this.timeline.clips) {
            const video = this.clipVideos.get(clip.path);
            if (!video) continue;
            
            // Seek to middle of clip
            video.currentTime = clip.duration / 2;
            
            await new Promise(resolve => {
                video.addEventListener('seeked', resolve, { once: true });
            });
            
            // Create thumbnail canvas
            const thumbCanvas = document.createElement('canvas');
            thumbCanvas.width = 160;
            thumbCanvas.height = 90;
            const thumbCtx = thumbCanvas.getContext('2d');
            
            // Draw scaled frame
            thumbCtx.drawImage(video, 0, 0, 160, 90);
            
            // Convert to data URL
            const dataUrl = thumbCanvas.toDataURL('image/jpeg', 0.7);
            thumbnails.set(clip.id || clip.path, dataUrl);
        }
        
        return thumbnails;
    }
    
    // Update timeline
    updateTimeline(newTimeline) {
        this.timeline = newTimeline;
        this.calculateDuration();
        
        // Reset playback if needed
        if (this.currentTime > this.duration) {
            this.currentTime = this.duration;
        }
        
        this.updatePlayhead();
        this.renderFrame();
    }
    
    // Cleanup
    destroy() {
        this.pause();
        
        // Clean up video elements
        for (const video of this.clipVideos.values()) {
            video.src = '';
            video.load();
        }
        
        this.clipVideos.clear();
        this.frameCache.clear();
    }
}

// Export for use in main timeline script
window.VideoPlayer = VideoPlayer;