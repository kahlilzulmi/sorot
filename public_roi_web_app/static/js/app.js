// ==============================================================================
// VIDEO ROI ANALYZER - Vue.js App
// ==============================================================================

const { createApp } = Vue;

createApp({
    data() {
        return {
            // Connection
            socket: null,
            statusMessage: 'Initializing...',
            
            // Application Mode
            appMode: 'select',  // 'select', 'live', 'import'
            
            // Import Mode Data
            importedGazeData: null,
            importedGazeFile: null,
            importedVideoFile: null,
            importedGazeVideoFile: null,  // Optional eye gaze video for dual-view mode
            videoMode: 'single',  // 'single' or 'dual'
            frameOffset: 0,  // Frame offset between gaze data and video
            showImportModal: false,
            importPreviewData: null,
            csvHeaders: [],  // Available CSV column headers
            csvRawLines: [],  // Raw CSV lines for re-parsing
            columnMapping: {  // User-selected column mapping
                frame: null,
                gazeX: null,
                gazeY: null
            },
            
            // Video state
            videoInfo: null,
            videoSrc: null,
            gazeVideoSrc: null,  // For dual-video mode
            currentFrame: 0,
            currentTime: 0,
            videoDuration: 0,
            playing: false,
            
            // YouTube download
            youtubeUrl: '',
            downloading: false,
            lastYoutubeUrl: '',  // Track last downloaded URL
            lastUpdated: null,  // Last save timestamp
            currentWorkspaceFile: null,  // Current workspace file name
            
            // Modals
            showNewVideoModal: false,  // Modal for New Video
            showRecordModal: false,  // Modal for Record disclaimer
            showProcessModal: false,  // Modal for Post-processing
            showProgressModal: false, // Modal for recording/post-processing progress
            showROIModal: false,  // Modal for ROI naming
            showSaveAsModal: false,  // Modal for Save As with rename
            saveAsFilename: '',  // Filename for Save As operation
            tempROI: null,  // Temporary ROI data before saving
            
            // Scenes & ROIs
            scenes: [],
            selectedSceneIdx: 0,
            selectedROIIdx: null,
            editingSceneIdx: null,  // Track which scene is being renamed
            editingROIIdx: null,    // Track which ROI is being renamed
            editingName: '',        // Temporary name during editing
            openSceneMenu: null,    // Track which scene menu is open
            openROIMenu: null,      // Track which ROI menu is open
            
            // History for undo/redo
            history: [],
            historyIndex: -1,
            
            // ROI drawing
            drawing: false,
            startX: 0,
            startY: 0,
            newROILabel: 'ROI',
            
            // ROI editing (drag & resize)
            editingROI: false,
            editROIIdx: null,
            resizeHandle: null,
            dragStartX: 0,
            dragStartY: 0,
            originalROI: null,
            hoverROIIdx: null,
            hoverHandle: null,
            
            // Boundary dragging
            draggingBoundary: false,
            dragBoundaryIdx: null,
            
            // Recording
            recording: false,
            framesRecorded: 0,
            lastGazeData: null,
            sessionDir: null,
            showRecordingOverlay: false,
            useMouseFallback: false,  // Track if using mouse instead of OBS
            lastMouseX: 0,  // Track mouse position for gaze fallback
            lastMouseY: 0,
            lastRecordedFrame: -1,  // Track last frame recorded to avoid duplicates
            recordingAnimationId: null,  // Track requestAnimationFrame ID
            
            // Post-processing
            processing: false,
            processingStatus: '',
            progressSteps: [],
            progressMessage: '',
            progressError: null,
            progressComplete: false,
            
            // ROI Color Palette
            roiColorPalette: [
                '#61AFEF', // Blue
                '#98C379', // Green
                '#E5C07B', // Yellow
                '#E06C75', // Red
                '#C678DD', // Purple
                '#56B6C2', // Cyan
                '#D19A66', // Orange
                '#BE5046', // Dark Red
            ],
            nextColorIndex: 0,
            
            // Scene Color Palette for Timeline
            sceneColorPalette: [
                { base: '#667eea', gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', name: 'Purple' },
                { base: '#f093fb', gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', name: 'Pink' },
                { base: '#4facfe', gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', name: 'Blue' },
                { base: '#43e97b', gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', name: 'Green' },
                { base: '#fa709a', gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', name: 'Sunset' },
                { base: '#30cfd0', gradient: 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)', name: 'Ocean' },
                { base: '#a8edea', gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', name: 'Pastel' },
                { base: '#ff9a56', gradient: 'linear-gradient(135deg, #ff9a56 0%, #ff6a88 100%)', name: 'Coral' },
                { base: '#ffecd2', gradient: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)', name: 'Peach' },
                { base: '#a1c4fd', gradient: 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)', name: 'Sky' },
            ],
        };
    },
    
    computed: {
        currentScene() {
            // Find scene that contains current frame
            for (let i = 0; i < this.scenes.length; i++) {
                const scene = this.scenes[i];
                // Use < for end_frame to avoid overlap at boundaries
                if (scene.start_frame <= this.currentFrame && this.currentFrame < scene.end_frame) {
                    return scene;
                }
            }
            // Check last scene separately (inclusive end)
            if (this.scenes.length > 0) {
                const lastScene = this.scenes[this.scenes.length - 1];
                if (this.currentFrame >= lastScene.start_frame && this.currentFrame <= lastScene.end_frame) {
                    return lastScene;
                }
            }
            return this.scenes[this.selectedSceneIdx] || null;
        },
        
        activeSceneIdx() {
            // Get index of scene containing current frame
            for (let i = 0; i < this.scenes.length; i++) {
                const scene = this.scenes[i];
                // Use < for end_frame to avoid overlap at boundaries
                if (scene.start_frame <= this.currentFrame && this.currentFrame < scene.end_frame) {
                    return i;
                }
            }
            // Check last scene separately (inclusive end)
            if (this.scenes.length > 0 && this.currentFrame >= this.scenes[this.scenes.length - 1].start_frame) {
                return this.scenes.length - 1;
            }
            return this.selectedSceneIdx;
        },
        
        canUndo() {
            return this.historyIndex > 0;
        },
        
        canRedo() {
            return this.historyIndex < this.history.length - 1;
        }
    },
    
    watch: {
        showROIModal(newVal) {
            if (newVal) {
                // Auto-focus input when modal opens
                this.$nextTick(() => {
                    if (this.$refs.roiLabelInput) {
                        this.$refs.roiLabelInput.focus();
                        this.$refs.roiLabelInput.select();
                    }
                });
            }
        },

        showProgressModal(newVal) {
            // When progress modal is up, close other modals to avoid stacking
            if (newVal) {
                this.showNewVideoModal = false;
                this.showRecordModal = false;
                this.showProcessModal = false;
                this.showROIModal = false;
            }
        },
        
        activeSceneIdx(newIdx) {
            // Auto-scroll to active scene when slider moves to different scene
            this.$nextTick(() => {
                const sceneElements = document.querySelectorAll('.scene-item');
                if (sceneElements[newIdx]) {
                    sceneElements[newIdx].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
        }
    },
    
    mounted() {
        // Ensure any stale processing UI is cleared on load/refresh
        this.resetProcessingState();
        this.initSocket();
        this.loadVideoInfo();
        this.statusMessage = 'Ready';
        
        // Close menus when clicking outside
        document.addEventListener('click', () => {
            this.closeAllMenus();
        });
        
        // Track mouse position for gaze fallback
        document.addEventListener('mousemove', (event) => {
            this.updateMousePosition(event);
        });
        
        // Global mouse up handler for ROI editing
        document.addEventListener('mouseup', () => {
            if (this.editingROI) {
                this.endEditROI();
            }
        });
        
        // Initialize Lucide icons
        this.$nextTick(() => {
            if (window.lucide) {
                lucide.createIcons();
            }
        });
    },
    
    updated() {
        // Reinitialize Lucide icons after DOM updates
        this.$nextTick(() => {
            if (window.lucide) {
                lucide.createIcons();
            }
        });
    },
    
    methods: {
        // Prevent opening other modals while processing is in progress
        canOpenModal() {
            return !(this.showProgressModal && !this.progressComplete && !this.progressError);
        },

        // Reset any processing/progress UI state (used when switching workspaces)
        resetProcessingState() {
            this.processing = false;
            this.processingStatus = '';
            this.showProgressModal = false;
            this.progressSteps = [];
            this.progressMessage = '';
            this.progressError = null;
            this.progressComplete = false;
        },
        
        // ==================================================================
        // MODE SELECTION & IMPORT
        // ==================================================================
        
        selectMode(mode) {
            if (mode === 'live') {
                this.appMode = 'live';
            } else if (mode === 'import') {
                this.appMode = 'import';
                this.showImportModal = true;
            }
        },
        
        backToModeSelect() {
            this.appMode = 'select';
            // Reset import state
            this.importedGazeData = null;
            this.importedGazeFile = null;
            this.importedVideoFile = null;
            this.importedGazeVideoFile = null;
            this.videoMode = 'single';
            this.frameOffset = 0;
            this.showImportModal = false;
            this.importPreviewData = null;
            this.csvHeaders = [];
            this.csvRawLines = [];
            this.columnMapping = { frame: null, gazeX: null, gazeY: null };
            // Reset video state
            this.clearVideo();
        },
        
        selectGazeCSV(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            this.importedGazeFile = file;
            this.importedGazeData = null;
            this.importPreviewData = null;
            
            // Parse CSV headers
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const text = e.target.result;
                    const lines = text.trim().split('\n');
                    
                    if (lines.length < 2) {
                        alert('CSV file is empty or invalid');
                        this.importedGazeFile = null;
                        return;
                    }
                    
                    // Store raw lines for later parsing
                    this.csvRawLines = lines;
                    
                    // Parse header
                    const header = lines[0].split(',').map(h => h.trim());
                    this.csvHeaders = header;
                    
                    // Try to auto-detect columns
                    const headerLower = header.map(h => h.toLowerCase());
                    let frameIdx = headerLower.indexOf('frame_num');
                    let xIdx = headerLower.indexOf('gaze_x');
                    let yIdx = headerLower.indexOf('gaze_y');
                    
                    // Try alternative column names
                    if (frameIdx === -1) {
                        frameIdx = headerLower.findIndex(h => h.includes('frame'));
                    }
                    if (xIdx === -1) {
                        xIdx = headerLower.findIndex(h => (h.includes('gaze') || h.includes('x')) && h.includes('x'));
                    }
                    if (yIdx === -1) {
                        yIdx = headerLower.findIndex(h => (h.includes('gaze') || h.includes('y')) && h.includes('y'));
                    }
                    
                    // Set auto-detected mapping (or use first 3 columns as fallback)
                    this.columnMapping = {
                        frame: frameIdx !== -1 ? frameIdx : 0,
                        gazeX: xIdx !== -1 ? xIdx : (header.length > 1 ? 1 : 0),
                        gazeY: yIdx !== -1 ? yIdx : (header.length > 2 ? 2 : 0)
                    };
                    
                    // Trigger preview update
                    this.updateCSVPreview();
                    
                } catch (error) {
                    console.error('Error parsing CSV:', error);
                    alert('Failed to parse CSV file: ' + error.message);
                    this.importedGazeFile = null;
                }
            };
            reader.readAsText(file);
        },
        
        updateCSVPreview() {
            if (!this.csvRawLines.length || this.columnMapping.frame === null) {
                return;
            }
            
            const frameIdx = this.columnMapping.frame;
            const xIdx = this.columnMapping.gazeX;
            const yIdx = this.columnMapping.gazeY;
            
            // Parse data rows
            let validPoints = 0;
            const gazeData = [];
            let invalidRows = 0;
            
            for (let i = 1; i < this.csvRawLines.length; i++) {
                const parts = this.csvRawLines[i].split(',');
                if (parts.length < Math.max(frameIdx, xIdx, yIdx) + 1) {
                    invalidRows++;
                    continue;
                }
                
                const frameNum = parseInt(parts[frameIdx]);
                const gazeX = parseFloat(parts[xIdx]);
                const gazeY = parseFloat(parts[yIdx]);
                
                if (!isNaN(frameNum) && !isNaN(gazeX) && !isNaN(gazeY)) {
                    gazeData.push({ frame_num: frameNum, gaze_x: gazeX, gaze_y: gazeY });
                    validPoints++;
                } else {
                    invalidRows++;
                }
            }
            
            if (gazeData.length === 0) {
                this.importPreviewData = null;
                return;
            }
            
            this.importedGazeData = gazeData;
            
            // Update preview
            this.importPreviewData = {
                total_frames: gazeData.length > 0 ? Math.max(...gazeData.map(d => d.frame_num)) + 1 : 0,
                valid_points: validPoints,
                invalid_rows: invalidRows,
                detection_rate: gazeData.length > 0 ? 
                    ((validPoints / (Math.max(...gazeData.map(d => d.frame_num)) + 1)) * 100).toFixed(1) : 0
            };
            
            if (invalidRows > 0) {
                console.warn(`Skipped ${invalidRows} invalid rows during CSV import`);
            }
        },
        
        selectImportVideo(event) {
            const file = event.target.files[0];
            if (!file) return;
            this.importedVideoFile = file;
        },
        
        selectGazeVideo(event) {
            const file = event.target.files[0];
            if (!file) return;
            this.importedGazeVideoFile = file;
        },
        
        async processImportedData() {
            if (!this.importedGazeFile || !this.importedVideoFile) {
                alert('Please select both gaze CSV and video file');
                return;
            }
            
            if (!this.importedGazeData || this.importedGazeData.length === 0) {
                alert('No valid gaze data. Please check column mapping.');
                return;
            }
            
            try {
                // Send parsed gaze data as JSON
                const response = await axios.post('/api/import-gaze-data', {
                    gaze_data: this.importedGazeData,
                    frame_offset: this.frameOffset
                });
                
                if (response.data.success) {
                    // Upload video
                    const videoFormData = new FormData();
                    videoFormData.append('video', this.importedVideoFile);
                    
                    const videoResponse = await axios.post('/api/upload-video', videoFormData, {
                        onUploadProgress: (progressEvent) => {
                            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                            console.log(`Upload progress: ${percent}%`);
                        }
                    });
                    
                    if (videoResponse.data && videoResponse.data.filename) {
                        // Load video and initialize scenes
                        this.videoInfo = videoResponse.data;
                        this.videoSrc = '/video_feed';
                        this.scenes = [];
                        this.selectedSceneIdx = 0;
                        this.showImportModal = false;
                        
                        // Upload gaze video if provided
                        if (this.importedGazeVideoFile) {
                            const gazeVideoFormData = new FormData();
                            gazeVideoFormData.append('video', this.importedGazeVideoFile);
                            
                            const gazeVideoResponse = await axios.post('/api/upload-gaze-video', gazeVideoFormData);
                            if (gazeVideoResponse.data && gazeVideoResponse.data.path) {
                                this.gazeVideoSrc = gazeVideoResponse.data.path;
                            }
                        }
                        
                        // Create single scene spanning entire video
                        this.addScene(0, this.videoInfo.total_frames - 1);
                        
                        let message = `Import successful!\n\n` +
                              `Video: ${videoResponse.data.filename}\n` +
                              `Gaze Points: ${response.data.gaze_points}\n` +
                              `Frame Offset: ${this.frameOffset}`;
                        
                        if (this.importedGazeVideoFile) {
                            message += `\n\nGaze video loaded - Use "Dual Video" button to view side-by-side`;
                        }
                        
                        message += `\n\nYou can now define ROIs and generate reports.`;
                        alert(message);
                    }
                } else {
                    alert('Failed to import gaze data: ' + response.data.message);
                }
                
            } catch (error) {
                console.error('Import error:', error);
                alert('Failed to process imported data: ' + (error.response?.data?.message || error.message));
            }
        },
        
        async generateReportsFromImport() {
            if (!this.importedGazeData) {
                alert('No imported gaze data available');
                return;
            }
            
            if (!this.videoInfo) {
                alert('No video loaded');
                return;
            }
            
            if (this.scenes.length === 0) {
                alert('Please define at least one scene with ROIs');
                return;
            }
            
            // Check if any scene has ROIs defined
            const hasROIs = this.scenes.some(scene => scene.rois && scene.rois.length > 0);
            if (!hasROIs) {
                const proceed = confirm('No ROIs defined. Generate reports anyway?');
                if (!proceed) return;
            }
            
            try {
                this.showProgressModal = true;
                this.progressMessage = 'Generating reports from imported data...';
                this.progressComplete = false;
                this.progressError = null;
                
                const response = await axios.post('/api/generate-reports-from-import');
                
                if (response.data.success) {
                    this.sessionDir = response.data.session_dir;
                    this.progressComplete = true;
                    this.progressMessage = `Reports generated successfully!\n\n` +
                        `Gaze points processed: ${response.data.gaze_points_processed}\n` +
                        `Excel: ${response.data.excel_report}\n` +
                        `PDF: ${response.data.pdf_report}`;
                    
                    // Refresh reports list
                    await this.loadReports();
                } else {
                    throw new Error(response.data.error || 'Unknown error');
                }
                
            } catch (error) {
                console.error('Report generation error:', error);
                this.progressError = 'Report generation failed: ' + (error.response?.data?.error || error.message);
            }
        },
        
        async loadReports() {
            try {
                const response = await axios.get('/api/reports/list');
                if (response.data && response.data.reports) {
                    console.log('Reports loaded:', response.data.reports.length);
                }
            } catch (error) {
                console.error('Failed to load reports:', error);
            }
        },
        
        // ==================================================================
        // WEBSOCKET
        // ==================================================================
        
        initSocket() {
            this.socket = io();
            
            this.socket.on('connect', () => {
                this.statusMessage = 'Connected';
                console.log('WebSocket connected');
            });
            
            this.socket.on('disconnect', () => {
                this.statusMessage = 'Disconnected';
                console.log('WebSocket disconnected');
            });
            
            this.socket.on('gaze_detected', (data) => {
                this.lastGazeData = data;
                this.framesRecorded++;
            });
        },
        
        // Track mouse position for gaze fallback during recording
        updateMousePosition(event) {
            // Get the video element to calculate coordinates relative to it
            const videoPlayer = this.$refs.videoPlayer;
            if (!videoPlayer || !this.videoInfo) {
                this.lastMouseX = event.clientX;
                this.lastMouseY = event.clientY;
                return;
            }
            
            const rect = videoPlayer.getBoundingClientRect();
            const scaleX = this.videoInfo.width / rect.width;
            const scaleY = this.videoInfo.height / rect.height;
            
            // Convert screen coordinates to video coordinates
            const videoX = (event.clientX - rect.left) * scaleX;
            const videoY = (event.clientY - rect.top) * scaleY;
            
            // Clamp to video bounds
            this.lastMouseX = Math.max(0, Math.min(Math.round(videoX), this.videoInfo.width - 1));
            this.lastMouseY = Math.max(0, Math.min(Math.round(videoY), this.videoInfo.height - 1));
        },
        
        // Get scene thumbnail URL
        getSceneThumbnailUrl(frameNum) {
            if (!this.videoInfo) return '';
            return `/api/thumbnail?video=${encodeURIComponent(this.videoInfo.filename)}&frame=${frameNum}`;
        },
        
        // Handle thumbnail loading errors
        handleThumbnailError(event) {
            event.target.style.display = 'none';
        },
        
        // Convert frame number to time string (MM:SS or HH:MM:SS)
        frameToTime(frameNum) {
            if (!this.videoInfo || !this.videoInfo.fps) return '00:00';
            const totalSeconds = Math.floor(frameNum / this.videoInfo.fps);
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;
            
            if (hours > 0) {
                return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }
            return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        },
        
        // ==================================================================
        // VIDEO LOADING
        // ==================================================================
        
        async uploadVideo(event) {
            const file = event.target.files[0];
            if (!file) return;

            // New video load should clear any lingering processing UI
            this.resetProcessingState();

            if (this.showProgressModal && !this.progressComplete && !this.progressError) {
                alert('Please wait until current processing finishes.');
                return;
            }
            
            this.statusMessage = 'Uploading video...';
            
            const formData = new FormData();
            formData.append('video', file);
            
            try {
                const response = await axios.post('/api/upload-video', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                
                this.videoInfo = response.data;
                this.videoSrc = `/video/${response.data.filename}`;
                await this.loadScenes();
                
                this.statusMessage = 'Video loaded';
                this.showNewVideoModal = false;  // Close modal
            } catch (error) {
                alert('Failed to upload video: ' + error.message);
                this.statusMessage = 'Upload failed';
            }
        },
        
        async downloadYoutube() {
            if (!this.youtubeUrl) {
                alert('Please enter a YouTube URL');
                return;
            }

            // Fresh download clears any stale processing UI
            this.resetProcessingState();

            if (this.showProgressModal && !this.progressComplete && !this.progressError) {
                alert('Please wait until current processing finishes.');
                return;
            }
            
            this.downloading = true;
            this.statusMessage = 'Downloading from YouTube...';
            
            try {
                const response = await axios.post('/api/download-youtube', {
                    url: this.youtubeUrl
                });
                
                this.videoInfo = response.data;
                this.videoSrc = `/video/${response.data.filename}`;
                await this.loadScenes();
                
                this.statusMessage = 'Video downloaded';
                this.lastYoutubeUrl = this.youtubeUrl;  // Save URL for export
                this.youtubeUrl = '';
                this.showNewVideoModal = false;  // Close modal
            } catch (error) {
                alert('Failed to download video: ' + error.response?.data?.error || error.message);
                this.statusMessage = 'Download failed';
            } finally {
                this.downloading = false;
            }
        },
        
        async loadVideoInfo() {
            try {
                const response = await axios.get('/api/video-info');
                this.videoInfo = response.data;
                this.videoSrc = `/video/${response.data.filename}`;
                await this.loadScenes();
            } catch (error) {
                // No video loaded yet
            }
        },
        
        async saveWorkspace() {
            if (!this.videoInfo) {
                alert('No workspace to save');
                return;
            }
            
            // Create workspace data
            const workspace = {
                version: '1.0',
                timestamp: new Date().toISOString(),
                video_info: this.videoInfo,
                scenes: this.scenes,
                youtube_url: this.lastYoutubeUrl || '',  // Save YouTube URL if used
                workspace_file: this.currentWorkspaceFile  // Send current file for overwrite
            };
            
            try {
                const response = await axios.post('/api/save-workspace', workspace);
                if (response.data.success) {
                    this.lastUpdated = response.data.last_updated;
                    this.currentWorkspaceFile = response.data.workspace_file;
                    this.statusMessage = `Saved to ${this.currentWorkspaceFile}`;
                    // Show brief notification
                    alert(`Workspace saved to ${this.currentWorkspaceFile}`);
                } else {
                    alert('Failed to save workspace');
                }
            } catch (error) {
                console.error('Save error:', error);
                alert('Error saving workspace: ' + (error.response?.data?.error || error.message));
            }
        },
        
        openSaveAsModal() {
            if (!this.videoInfo) {
                alert('No workspace to save');
                return;
            }
            
            // Suggest current filename or generate new one
            if (this.currentWorkspaceFile) {
                // Remove .json extension for editing
                this.saveAsFilename = this.currentWorkspaceFile.replace(/\.json$/, '');
            } else {
                // Generate default name with timestamp
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
                this.saveAsFilename = `workspace_${timestamp}`;
            }
            
            this.showSaveAsModal = true;
        },
        
        async confirmSaveAs() {
            if (!this.saveAsFilename.trim()) {
                alert('Please enter a filename');
                return;
            }
            
            // Create workspace data
            const workspace = {
                version: '1.0',
                timestamp: new Date().toISOString(),
                video_info: this.videoInfo,
                scenes: this.scenes,
                youtube_url: this.lastYoutubeUrl || '',
                filename: this.saveAsFilename.trim()
            };
            
            try {
                const response = await axios.post('/api/save-workspace-as', workspace);
                if (response.data.success) {
                    this.lastUpdated = response.data.last_updated;
                    this.currentWorkspaceFile = response.data.workspace_file;
                    this.statusMessage = `Saved as ${this.currentWorkspaceFile}`;
                    this.showSaveAsModal = false;
                    alert(`Workspace saved as ${this.currentWorkspaceFile}`);
                } else {
                    alert('Failed to save workspace');
                }
            } catch (error) {
                console.error('Save As error:', error);
                const errorMsg = error.response?.data?.error || error.message;
                alert('Error: ' + errorMsg);
            }
        },
        
        async exportScenesROIs(format = 'csv', customFilename = null) {
            /**
             * Export scenes and ROIs data to CSV or JSON format.
             * 
             * @param {string} format - Export format: 'csv' or 'json'
             * @param {string} customFilename - Optional custom filename (without extension)
             * 
             * CSV format: Flat table with one row per ROI (or scene if no ROIs)
             * JSON format: Nested structure with full metadata and timestamps
             */
            if (!this.videoInfo || !this.scenes || this.scenes.length === 0) {
                alert('No scenes to export. Please define scenes first.');
                return;
            }
            
            try {
                const filename = customFilename || `scenes_rois_${this.videoInfo.filename.replace(/\.[^/.]+$/, '')}`;
                
                const payload = {
                    scenes: this.scenes,
                    video_info: this.videoInfo,
                    format: format,
                    filename: filename,
                    include_normalized: true,
                    include_timestamps: true
                };
                
                this.statusMessage = `Exporting as ${format.toUpperCase()}...`;
                
                const response = await axios.post('/api/export-scenes-rois', payload);
                
                if (response.data.success) {
                    const result = response.data;
                    
                    // Show success message
                    const message = format === 'csv' 
                        ? `✅ Exported ${result.rows} rows to CSV\n\n` +
                          `Scenes: ${result.scenes}\n` +
                          `Total ROIs: ${result.total_rois}\n\n` +
                          `File: ${result.filename}`
                        : `✅ Exported to JSON\n\n` +
                          `Scenes: ${result.scenes}\n` +
                          `Total ROIs: ${result.total_rois}\n\n` +
                          `File: ${result.filename}`;
                    
                    alert(message);
                    this.statusMessage = `Exported to ${result.filename}`;
                    
                    // Optionally download the file directly
                    // You could add a download link here if the backend serves the file
                    
                } else {
                    throw new Error(response.data.error || 'Export failed');
                }
                
            } catch (error) {
                console.error('Export error:', error);
                const errorMsg = error.response?.data?.error || error.message;
                alert('Export failed: ' + errorMsg);
                this.statusMessage = 'Export failed';
            }
        },
        
        openExportModal() {
            /**
             * Show a modal to choose export format and options.
             * This is a simple implementation - you can enhance the UI.
             */
            if (!this.videoInfo || !this.scenes || this.scenes.length === 0) {
                alert('No scenes to export. Please define scenes first.');
                return;
            }
            
            const format = prompt(
                'Choose export format:\n\n' +
                '1 = CSV (flat table, good for Excel/analysis)\n' +
                '2 = JSON (structured data, good for programming)\n\n' +
                'Enter 1 or 2:',
                '1'
            );
            
            if (format === null) return; // Cancelled
            
            const selectedFormat = format === '2' ? 'json' : 'csv';
            
            const customName = prompt(
                `Export as ${selectedFormat.toUpperCase()}\n\n` +
                'Enter custom filename (optional, leave blank for auto-generated):',
                ''
            );
            
            if (customName === null) return; // Cancelled
            
            this.exportScenesROIs(selectedFormat, customName.trim() || null);
        },
        
        async importWorkspace(event) {
            const file = event.target.files[0];
            if (!file) return;

            // Clean processing/progress state when loading a new workspace
            this.resetProcessingState();

            if (this.showProgressModal && !this.progressComplete && !this.progressError) {
                alert('Please wait until current processing finishes.');
                event.target.value = '';
                return;
            }
            
            try {
                const text = await file.text();
                const workspace = JSON.parse(text);
                
                // Validate workspace format
                if (!workspace.video_info || !workspace.scenes) {
                    alert('Invalid workspace file format');
                    return;
                }
                
                // Check if video file exists
                const videoFilename = workspace.video_info.filename;
                const videoPath = workspace.video_info.path;
                
                // Try to load the video
                try {
                    const response = await axios.post('/api/import-workspace', workspace);
                    
                    if (response.data.success) {
                        const resolvedVideoInfo = response.data.video_info || workspace.video_info;
                        const resolvedScenes = response.data.scenes || workspace.scenes;
                        
                        // Ensure backward compatibility: add custom_name field if missing
                        resolvedScenes.forEach(scene => {
                            if (!scene.hasOwnProperty('custom_name')) {
                                scene.custom_name = '';
                            }
                        });
                        
                        this.videoInfo = resolvedVideoInfo;
                        this.videoSrc = `/video/${resolvedVideoInfo.filename}`;
                        this.scenes = resolvedScenes;
                        this.lastUpdated = response.data.last_updated || new Date().toISOString();
                        this.currentWorkspaceFile = file.name;  // Store the loaded workspace filename
                        
                        // Initialize history
                        this.history = [JSON.parse(JSON.stringify(this.scenes))];
                        this.historyIndex = 0;
                        
                        // Reload video player
                        this.$nextTick(() => {
                            const video = this.$refs.videoPlayer;
                            if (video) {
                                video.load();
                            }
                        });
                        
                        if (response.data.downloaded_from_url) {
                            this.statusMessage = 'Workspace imported (video auto-downloaded)';
                            alert('Workspace imported. The video was missing, so it was auto-downloaded from the saved URL.');
                        } else {
                            this.statusMessage = 'Workspace imported';
                            alert('Workspace imported successfully!');
                        }
                    } else {
                        // Video not found - show detailed instructions
                        const videoInfo = workspace.video_info;
                        const youtubeUrl = workspace.youtube_url || '';
                        
                        let message = `⚠️ VIDEO FILE NOT FOUND\n\n`;
                        message += `Required video: "${videoFilename}"\n`;
                        message += `Resolution: ${videoInfo.width}x${videoInfo.height}\n`;
                        message += `Duration: ${videoInfo.duration.toFixed(2)}s\n`;
                        message += `FPS: ${videoInfo.fps.toFixed(2)}\n\n`;
                        
                        if (youtubeUrl) {
                            message += `📺 This workspace was created from YouTube URL:\n${youtubeUrl}\n\n`;
                            message += `INSTRUCTIONS:\n`;
                            message += `1. Copy the YouTube URL above\n`;
                            message += `2. Paste it in the YouTube URL field\n`;
                            message += `3. Click "Download" button\n`;
                            message += `4. After download completes, import this workspace again`;
                        } else {
                            message += `📁 This workspace was created from uploaded file.\n\n`;
                            message += `INSTRUCTIONS:\n`;
                            message += `1. Upload the EXACT SAME video file: "${videoFilename}"\n`;
                            message += `2. After upload completes, import this workspace again\n\n`;
                            message += `⚠️ The video MUST be identical (same name, duration, resolution)`;
                        }
                        
                        alert(message);
                        
                        // Pre-fill YouTube URL if available
                        if (youtubeUrl) {
                            this.youtubeUrl = youtubeUrl;
                        }
                    }
                } catch (error) {
                    const backendMsg = error.response?.data?.error || error.message;
                    alert('Failed to import workspace: ' + backendMsg);
                }
                
            } catch (error) {
                alert('Failed to read workspace file: ' + error.message);
            }
            
            // Reset file input
            event.target.value = '';
        },
        
        onVideoLoaded() {
            const video = this.$refs.videoPlayer;
            this.videoDuration = video.duration;
            this.currentTime = 0;
            this.currentFrame = 0;
            
            // Setup canvas
            const canvas = this.$refs.roiCanvas;
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Add event listeners to sync playing state with video element
            video.addEventListener('play', () => {
                this.playing = true;
                this.$nextTick(() => lucide.createIcons());
            });
            video.addEventListener('pause', () => {
                this.playing = false;
                this.$nextTick(() => lucide.createIcons());
            });
            video.addEventListener('ended', () => {
                this.playing = false;
                this.$nextTick(() => lucide.createIcons());
            });
            
            // Auto-create second scene if only one exists
            if (this.scenes.length === 1 && this.videoInfo) {
                const firstScene = this.scenes[0];
                const totalFrames = this.videoInfo.total_frames;
                
                // Split at 50% if scene covers entire video
                if (firstScene.start_frame === 0 && firstScene.end_frame === totalFrames - 1) {
                    const midPoint = Math.floor(totalFrames / 2);
                    firstScene.end_frame = midPoint - 1;
                    
                    this.scenes.push({
                        start_frame: midPoint,
                        end_frame: totalFrames - 1,
                        name: 'Scene 2',
                        rois: []
                    });
                    
                    this.saveScenes(true); // Save without history
                }
            }
            
            this.renderROIs();
        },
        
        onTimeUpdate() {
            // Only update UI state - recording is handled by per-frame loop
            const video = this.$refs.videoPlayer;
            this.currentTime = video.currentTime;
            this.currentFrame = Math.floor(video.currentTime * this.videoInfo.fps);
            
            // Sync playing state with video element
            const isPlaying = !video.paused;
            if (this.playing !== isPlaying) {
                this.playing = isPlaying;
                this.$nextTick(() => lucide.createIcons());
            }
            
            this.renderROIs();
            
            // Sync gaze video with offset in dual mode
            if (this.videoMode === 'dual' && this.appMode === 'import' && this.$refs.gazeVideoPlayer) {
                this.applyOffsetToGazeVideo();
            }
        },
        
        recordingFrameLoop() {
            if (!this.recording) {
                this.recordingAnimationId = null;
                return;
            }
            
            const video = this.$refs.videoPlayer;
            if (!video || !this.videoInfo) {
                this.recordingAnimationId = requestAnimationFrame(() => this.recordingFrameLoop());
                return;
            }
            
            // Calculate current frame from video time
            const currentFrame = Math.floor(video.currentTime * this.videoInfo.fps);
            
            // Only record when frame changes (avoid duplicates)
            if (currentFrame !== this.lastRecordedFrame) {
                this.lastRecordedFrame = currentFrame;
                this.framesRecorded++;
                
                // Get current scene and ROI
                const currentScene = this.currentScene;
                const roi = this.findROIAtPosition(this.lastMouseX, this.lastMouseY);
                
                // Send frame sync data (for OBS mode)
                const recordData = {
                    frame_num: currentFrame,
                    timestamp: video.currentTime
                };
                this.socket.emit('record_frame', recordData);
                
                // If using mouse fallback, send mouse position as gaze data
                if (this.useMouseFallback) {
                    const mouseGazeData = {
                        frame_num: currentFrame,
                        mouse_x: this.lastMouseX,
                        mouse_y: this.lastMouseY,
                        roi_label: roi ? roi.label : 'background',
                        scene_name: currentScene ? currentScene.name : 'unknown',
                        scene_custom_name: currentScene ? (currentScene.custom_name || '') : ''
                    };
                    this.socket.emit('record_mouse_gaze', mouseGazeData);
                }
                
                // Check if video ended
                if (video.ended || currentFrame >= this.videoInfo.total_frames - 1) {
                    this.autoStopRecording();
                    return;
                }
            }
            
            // Continue loop
            this.recordingAnimationId = requestAnimationFrame(() => this.recordingFrameLoop());
        },
        
        // ==================================================================
        // PLAYBACK CONTROLS
        // ==================================================================
        
        togglePlayback() {
            const video = this.$refs.videoPlayer;
            const gazeVideo = this.$refs.gazeVideoPlayer;
            
            if (this.playing) {
                video.pause();
                if (gazeVideo && this.videoMode === 'dual') {
                    gazeVideo.pause();
                }
            } else {
                video.play();
                if (gazeVideo && this.videoMode === 'dual') {
                    gazeVideo.play();
                }
            }
            // Note: playing state is automatically updated by video event listeners
        },
        
        seekToFrame() {
            const video = this.$refs.videoPlayer;
            const gazeVideo = this.$refs.gazeVideoPlayer;
            video.currentTime = this.currentFrame / this.videoInfo.fps;
            if (gazeVideo && this.videoMode === 'dual') {
                this.applyOffsetToGazeVideo();
            }
        },
        
        applyOffsetToGazeVideo() {
            const video = this.$refs.videoPlayer;
            const gazeVideo = this.$refs.gazeVideoPlayer;
            
            if (!gazeVideo || !video || !this.videoInfo) return;
            
            // Calculate gaze video time with offset
            // Positive offset means gaze video is ahead, so we need to add time to gaze video
            const offsetSeconds = this.frameOffset / this.videoInfo.fps;
            const gazeTime = video.currentTime + offsetSeconds;
            
            // Clamp to valid range
            if (gazeTime >= 0 && gazeTime <= gazeVideo.duration) {
                gazeVideo.currentTime = gazeTime;
            }
        },
        
        adjustOffset(delta) {
            this.frameOffset += delta;
            this.applyOffsetToGazeVideo();
        },
        
        nextFrame() {
            if (this.currentFrame < this.videoInfo.total_frames - 1) {
                const video = this.$refs.videoPlayer;
                
                // Pause if playing
                if (this.playing) {
                    video.pause();
                    this.playing = false;
                }
                
                // Increment frame and seek with small offset to force frame change
                this.currentFrame++;
                video.currentTime = (this.currentFrame / this.videoInfo.fps) + 0.001;
                
                // Force video to load the frame
                video.pause();
            }
        },
        
        prevFrame() {
            if (this.currentFrame > 0) {
                const video = this.$refs.videoPlayer;
                
                // Pause if playing
                if (this.playing) {
                    video.pause();
                    this.playing = false;
                }
                
                // Decrement frame and seek with small offset
                this.currentFrame--;
                video.currentTime = (this.currentFrame / this.videoInfo.fps) + 0.001;
                
                // Force video to load the frame
                video.pause();
            }
        },
        
        jumpToStart() {
            const video = this.$refs.videoPlayer;
            
            // Pause if playing
            if (this.playing) {
                video.pause();
                this.playing = false;
            }
            
            // Jump to first frame
            this.currentFrame = 0;
            video.currentTime = 0.001;
            video.pause();
        },
        
        jumpToEnd() {
            const video = this.$refs.videoPlayer;
            
            // Pause if playing
            if (this.playing) {
                video.pause();
                this.playing = false;
            }
            
            // Jump to last frame
            this.currentFrame = this.videoInfo.total_frames - 1;
            video.currentTime = (this.currentFrame / this.videoInfo.fps) + 0.001;
            video.pause();
        },
        
        prevScene() {
            if (!this.scenes || this.scenes.length === 0) return;
            
            const video = this.$refs.videoPlayer;
            
            // Pause if playing
            if (this.playing) {
                video.pause();
                this.playing = false;
            }
            
            // Find the previous scene
            let targetSceneIdx = -1;
            for (let i = this.scenes.length - 1; i >= 0; i--) {
                if (this.scenes[i].start_frame < this.currentFrame) {
                    targetSceneIdx = i;
                    break;
                }
            }
            
            // If found, jump to its start frame
            if (targetSceneIdx >= 0) {
                this.currentFrame = this.scenes[targetSceneIdx].start_frame;
                video.currentTime = (this.currentFrame / this.videoInfo.fps) + 0.001;
                this.selectedSceneIdx = targetSceneIdx;
                video.pause();
            }
        },
        
        nextScene() {
            if (!this.scenes || this.scenes.length === 0) return;
            
            const video = this.$refs.videoPlayer;
            
            // Pause if playing
            if (this.playing) {
                video.pause();
                this.playing = false;
            }
            
            // Find the next scene
            let targetSceneIdx = -1;
            for (let i = 0; i < this.scenes.length; i++) {
                if (this.scenes[i].start_frame > this.currentFrame) {
                    targetSceneIdx = i;
                    break;
                }
            }
            
            // If found, jump to its start frame
            if (targetSceneIdx >= 0) {
                this.currentFrame = this.scenes[targetSceneIdx].start_frame;
                video.currentTime = (this.currentFrame / this.videoInfo.fps) + 0.001;
                this.selectedSceneIdx = targetSceneIdx;
                video.pause();
            }
        },
        
        getSceneBoundaryStyle(scene, idx) {
            if (!this.videoInfo) return {};
            
            const totalFrames = this.videoInfo.total_frames;
            const leftPercent = (scene.start_frame / totalFrames) * 100;
            const widthPercent = ((scene.end_frame - scene.start_frame + 1) / totalFrames) * 100;
            
            // Get color from palette
            const colorScheme = this.sceneColorPalette[idx % this.sceneColorPalette.length];
            const isActive = this.activeSceneIdx === idx;
            const isSelected = this.selectedSceneIdx === idx;
            
            return {
                left: leftPercent + '%',
                width: widthPercent + '%',
                background: colorScheme.gradient,
                opacity: isActive ? '1' : '0.7',
                borderTop: isSelected ? '3px solid #fff' : 'none',
                borderBottom: isSelected ? '3px solid #fff' : 'none',
                boxShadow: isActive ? '0 2px 8px rgba(0,0,0,0.4)' : 'none',
                zIndex: isActive ? '10' : '5',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
            };
        },
        
        getSceneColor(idx) {
            return this.sceneColorPalette[idx % this.sceneColorPalette.length];
        },
        
        getSceneTooltip(scene, idx) {
            const duration = ((scene.end_frame - scene.start_frame + 1) / this.videoInfo.fps).toFixed(1);
            const roiCount = scene.rois ? scene.rois.length : 0;
            return `${scene.custom_name || scene.name}\n${scene.start_frame}-${scene.end_frame} (${duration}s)\n${roiCount} ROI${roiCount !== 1 ? 's' : ''}`;
        },
        
        jumpToScene(idx) {
            if (idx < 0 || idx >= this.scenes.length) return;
            const scene = this.scenes[idx];
            this.selectScene(idx);
            this.currentFrame = scene.start_frame;
            this.seekToFrame();
        },
        
        onSceneSegmentClick(idx) {
            this.jumpToScene(idx);
        },
        
        getBoundaryHandleStyle(scene) {
            if (!this.videoInfo) return {};
            
            const totalFrames = this.videoInfo.total_frames;
            const leftPercent = ((scene.end_frame + 1) / totalFrames) * 100;
            
            return {
                left: leftPercent + '%'
            };
        },
        
        startDragBoundary(event, boundaryIdx) {
            event.preventDefault();
            event.stopPropagation();
            
            this.draggingBoundary = true;
            this.dragBoundaryIdx = boundaryIdx;
            
            // Add global listeners - bind this context
            this.boundDragHandler = this.onDragBoundary.bind(this);
            this.boundStopHandler = this.stopDragBoundary.bind(this);
            
            document.addEventListener('mousemove', this.boundDragHandler);
            document.addEventListener('mouseup', this.boundStopHandler);
        },
        
        onDragBoundary(event) {
            if (!this.draggingBoundary || !this.videoInfo) return;
            
            // Find the slider element
            const sliderContainer = document.querySelector('.slider-container');
            if (!sliderContainer) return;
            
            const rect = sliderContainer.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const percent = Math.max(0, Math.min(1, x / rect.width));
            const newFrame = Math.round(percent * (this.videoInfo.total_frames - 1));
            
            const currentScene = this.scenes[this.dragBoundaryIdx];
            const nextScene = this.scenes[this.dragBoundaryIdx + 1];
            
            // Ensure minimum scene length (at least 10 frames)
            const minFrame = currentScene.start_frame + 10;
            const maxFrame = nextScene.end_frame - 10;
            
            if (newFrame >= minFrame && newFrame <= maxFrame) {
                currentScene.end_frame = newFrame;
                nextScene.start_frame = newFrame + 1;
            }
        },
        
        stopDragBoundary() {
            if (this.draggingBoundary) {
                this.draggingBoundary = false;
                this.dragBoundaryIdx = null;
                
                // Force thumbnail update after boundary change
                this.$forceUpdate();
                
                // Remove global listeners
                document.removeEventListener('mousemove', this.boundDragHandler);
                document.removeEventListener('mouseup', this.boundStopHandler);
                
                // Save changes
                this.saveScenes();
            }
        },
        
        formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        },
        
        formatTimestamp(isoString) {
            if (!isoString) return '';
            const date = new Date(isoString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            
            if (diffMins < 1) return 'baru saja';
            if (diffMins < 60) return `${diffMins} menit lalu`;
            
            const diffHours = Math.floor(diffMins / 60);
            if (diffHours < 24) return `${diffHours} jam lalu`;
            
            // Format as date
            const day = date.getDate().toString().padStart(2, '0');
            const month = (date.getMonth() + 1).toString().padStart(2, '0');
            const year = date.getFullYear();
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            return `${day}/${month}/${year} ${hours}:${minutes}`;
        },
        
        // ==================================================================
        // SCENE MANAGEMENT
        // ==================================================================
        
        async loadScenes() {
            try {
                const response = await axios.get('/api/scenes');
                this.scenes = response.data;
                this.selectedSceneIdx = 0;
                
                // Auto-create "rest of video" scene if only one scene exists
                if (this.scenes.length === 1 && this.videoInfo) {
                    const firstScene = this.scenes[0];
                    if (firstScene.end_frame < this.videoInfo.total_frames - 1) {
                        this.scenes.push({
                            start_frame: firstScene.end_frame + 1,
                            end_frame: this.videoInfo.total_frames - 1,
                            name: 'Rest of Video',
                            rois: []
                        });
                        await this.saveScenes(true); // Save without adding to history
                    }
                }
                
                // Initialize history with loaded state
                this.history = [JSON.parse(JSON.stringify(this.scenes))];
                this.historyIndex = 0;
            } catch (error) {
                console.error('Failed to load scenes:', error);
            }
        },
        
        saveToHistory() {
            // Remove any future history if we're not at the end
            if (this.historyIndex < this.history.length - 1) {
                this.history = this.history.slice(0, this.historyIndex + 1);
            }
            
            // Add current state to history
            this.history.push(JSON.parse(JSON.stringify(this.scenes)));
            this.historyIndex++;
            
            // Limit history size to 50 states
            if (this.history.length > 50) {
                this.history.shift();
                this.historyIndex--;
            }
        },
        
        async saveScenes(skipHistory = false) {
            try {
                if (!skipHistory) {
                    this.saveToHistory();
                }
                await axios.post('/api/scenes', this.scenes);
            } catch (error) {
                console.error('Failed to save scenes:', error);
            }
        },
        
        undo() {
            if (this.canUndo) {
                this.historyIndex--;
                this.scenes = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
                this.saveScenes(true); // Save to backend but skip history
                this.renderROIs();
            }
        },
        
        redo() {
            if (this.canRedo) {
                this.historyIndex++;
                this.scenes = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
                this.saveScenes(true); // Save to backend but skip history
                this.renderROIs();
            }
        },
        
        selectScene(idx) {
            this.selectedSceneIdx = idx;
            this.selectedROIIdx = null;
            
            // Jump to scene start frame
            const scene = this.scenes[idx];
            if (scene) {
                this.currentFrame = scene.start_frame;
                this.seekToFrame();
            }
            
            // Auto-scroll to selected scene in sidebar
            this.$nextTick(() => {
                const sceneElements = document.querySelectorAll('.scene-item');
                if (sceneElements[idx]) {
                    sceneElements[idx].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            });
            
            this.renderROIs();
        },
        
        async splitScene() {
            if (!this.videoInfo) return;
            
            // Find scene containing current frame
            let sceneIdx = -1;
            let scene = null;
            
            for (let i = 0; i < this.scenes.length; i++) {
                if (this.scenes[i].start_frame <= this.currentFrame && 
                    this.currentFrame <= this.scenes[i].end_frame) {
                    sceneIdx = i;
                    scene = this.scenes[i];
                    break;
                }
            }
            
            if (!scene) {
                alert('No scene found at current frame');
                return;
            }
            
            const splitFrame = this.currentFrame;
            
            if (splitFrame <= scene.start_frame || splitFrame >= scene.end_frame) {
                alert('Cannot split at this frame. Choose a frame within the scene range.');
                return;
            }
            
            // Create two new scenes
            const scene1 = {
                start_frame: scene.start_frame,
                end_frame: splitFrame - 1,
                name: `Scene ${sceneIdx + 1}`,
                custom_name: scene.custom_name || '',
                rois: [...scene.rois]
            };
            
            const scene2 = {
                start_frame: splitFrame,
                end_frame: scene.end_frame,
                name: `Scene ${sceneIdx + 2}`,
                custom_name: '',
                rois: []
            };
            
            // Replace current scene with two new scenes
            this.scenes.splice(sceneIdx, 1, scene1, scene2);
            
            // Renumber all subsequent scenes
            for (let i = sceneIdx + 2; i < this.scenes.length; i++) {
                this.scenes[i].name = `Scene ${i + 1}`;
            }
            
            await this.saveScenes();
        },
        
        async addScene() {
            const lastScene = this.scenes[this.scenes.length - 1];
            const startFrame = lastScene ? lastScene.end_frame + 1 : 0;
            
            this.scenes.push({
                start_frame: startFrame,
                end_frame: this.videoInfo.total_frames - 1,
                name: `Scene ${this.scenes.length + 1}`,
                custom_name: '',
                rois: []
            });
            
            await this.saveScenes();
        },
        
        async deleteScene(idx) {
            if (this.scenes.length <= 1) {
                alert('Cannot delete the only scene');
                return;
            }
            
            if (confirm(`Delete ${this.scenes[idx].name}?`)) {
                const deletedScene = this.scenes[idx];
                
                // If deleting a middle scene, merge gap with previous scene
                if (idx > 0 && idx < this.scenes.length - 1) {
                    // Extend previous scene to cover deleted scene's range
                    this.scenes[idx - 1].end_frame = this.scenes[idx + 1].start_frame - 1;
                } else if (idx > 0) {
                    // Deleting last scene - extend previous scene to video end
                    this.scenes[idx - 1].end_frame = this.videoInfo.total_frames - 1;
                } else if (idx === 0 && this.scenes.length > 1) {
                    // Deleting first scene - extend next scene to video start
                    this.scenes[1].start_frame = 0;
                }
                
                // Remove the scene
                this.scenes.splice(idx, 1);
                this.selectedSceneIdx = Math.min(this.selectedSceneIdx, this.scenes.length - 1);
                await this.saveScenes();
                this.renderROIs();
            }
        },
        
        async mergeWithPrevious() {
            if (this.selectedSceneIdx === 0) {
                alert('Cannot merge first scene');
                return;
            }
            
            const currentScene = this.scenes[this.selectedSceneIdx];
            const previousScene = this.scenes[this.selectedSceneIdx - 1];
            
            if (confirm(`Merge "${currentScene.name}" into "${previousScene.name}"?`)) {
                // Extend previous scene to cover current scene's range
                previousScene.end_frame = currentScene.end_frame;
                
                // Merge ROIs from current scene into previous scene
                previousScene.rois.push(...currentScene.rois);
                
                // Remove current scene
                this.scenes.splice(this.selectedSceneIdx, 1);
                
                // Select the merged scene
                this.selectedSceneIdx--;
                
                await this.saveScenes();
                this.renderROIs();
            }
        },
        
        startRenameScene(idx) {
            this.editingSceneIdx = idx;
            this.editingCustomName = this.scenes[idx].custom_name || '';
            
            // Focus input on next tick
            this.$nextTick(() => {
                const input = document.querySelector(`#scene-input-${idx}`);
                if (input) {
                    input.focus();
                    input.select();
                }
            });
        },
        
        async finishRenameScene(idx) {
            // Prevent duplicate calls
            if (this.editingSceneIdx !== idx) return;
            
            // Store the new custom name
            const customName = this.editingCustomName.trim();
            
            // Vue 3 has automatic reactivity - just assign directly
            this.scenes[idx].custom_name = customName;
            
            // Clear editing state first
            this.editingSceneIdx = null;
            this.editingCustomName = '';
            
            // Blur the input after clearing state
            this.$nextTick(() => {
                const input = document.querySelector(`#scene-input-${idx}`);
                if (input) input.blur();
            });
            
            // Save to backend
            await this.saveScenes();
        },
        
        cancelRenameScene() {
            this.editingSceneIdx = null;
            this.editingCustomName = '';
        },
        
        toggleSceneMenu(idx) {
            if (this.openSceneMenu === idx) {
                this.openSceneMenu = null;
            } else {
                this.openSceneMenu = idx;
                this.openROIMenu = null;  // Close ROI menu if open
            }
        },
        
        closeAllMenus() {
            this.openSceneMenu = null;
            this.openROIMenu = null;
        },
        
        // ==================================================================
        // ROI MANAGEMENT
        // ==================================================================
        
        startDrawROI(event) {
            if (!this.currentScene || this.recording || this.showRecordingOverlay) return;
            
            const canvas = this.$refs.roiCanvas;
            const rect = canvas.getBoundingClientRect();
            const mouseX = (event.clientX - rect.left) * (canvas.width / rect.width);
            const mouseY = (event.clientY - rect.top) * (canvas.height / rect.height);
            
            // Check if clicking on existing ROI
            const roiHit = this.getROIAtPoint(mouseX, mouseY);
            if (roiHit !== null) {
                // Start editing existing ROI
                this.startEditROI(roiHit, mouseX, mouseY);
                return;
            }
            
            // Start drawing new ROI
            this.drawing = true;
            this.startX = mouseX;
            this.startY = mouseY;
        },
        
        drawingROI(event) {
            if (this.recording) return;
            
            const canvas = this.$refs.roiCanvas;
            const rect = canvas.getBoundingClientRect();
            const mouseX = (event.clientX - rect.left) * (canvas.width / rect.width);
            const mouseY = (event.clientY - rect.top) * (canvas.height / rect.height);
            
            // Handle ROI editing (drag/resize)
            if (this.editingROI) {
                this.editingROIMove(mouseX, mouseY);
                return;
            }
            
            // Update hover state for cursor styling
            if (!this.drawing) {
                this.updateHoverState(mouseX, mouseY);
                return;
            }
            
            // Drawing new ROI
            const ctx = canvas.getContext('2d');
            
            // Clear and redraw
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.renderROIs();
            
            // Draw current rectangle
            ctx.strokeStyle = '#00ff00';
            ctx.lineWidth = 3;
            ctx.strokeRect(
                this.startX,
                this.startY,
                mouseX - this.startX,
                mouseY - this.startY
            );
        },
        
        async endDrawROI(event) {
            if (!this.drawing) return;
            this.drawing = false;
            
            const canvas = this.$refs.roiCanvas;
            const rect = canvas.getBoundingClientRect();
            
            const endX = (event.clientX - rect.left) * (canvas.width / rect.width);
            const endY = (event.clientY - rect.top) * (canvas.height / rect.height);
            
            const x = Math.min(this.startX, endX);
            const y = Math.min(this.startY, endY);
            const width = Math.abs(endX - this.startX);
            const height = Math.abs(endY - this.startY);
            
            if (width < 10 || height < 10) {
                return; // Too small
            }
            
            // Store temporary ROI data and show modal
            this.tempROI = {
                x: Math.round(x),
                y: Math.round(y),
                width: Math.round(width),
                height: Math.round(height),
                angle: 0
            };
            
            this.newROILabel = 'ROI';  // Default label
            this.showROIModal = true;
        },
        
        async saveROI() {
            if (!this.tempROI || !this.newROILabel) {
                alert('Please enter ROI label');
                return;
            }
            
            // Assign color from palette
            const color = this.roiColorPalette[this.nextColorIndex % this.roiColorPalette.length];
            this.nextColorIndex++;
            
            // Add ROI with label and color
            this.currentScene.rois.push({
                ...this.tempROI,
                label: this.newROILabel,
                color_tag: color
            });
            
            await this.saveScenes();
            this.renderROIs();
            
            // Reset
            this.showROIModal = false;
            this.tempROI = null;
            this.newROILabel = 'ROI';
        },
        
        cancelROI() {
            this.showROIModal = false;
            this.tempROI = null;
            this.renderROIs();  // Clear temporary drawing
        },
        
        selectROI(idx) {
            this.selectedROIIdx = idx;
            this.renderROIs();
        },
        
        async deleteROI(idx) {
            if (confirm(`Delete ${this.currentScene.rois[idx].label}?`)) {
                this.currentScene.rois.splice(idx, 1);
                this.selectedROIIdx = null;
                await this.saveScenes();
                this.renderROIs();
            }
        },
        
        startRenameROI(idx) {
            this.editingROIIdx = idx;
            this.editingName = this.currentScene.rois[idx].label;
            
            // Focus input on next tick
            this.$nextTick(() => {
                const input = document.querySelector(`#roi-input-${idx}`);
                if (input) {
                    input.focus();
                    input.select();
                }
            });
        },
        
        async finishRenameROI(idx) {
            if (this.editingName && this.editingName.trim()) {
                this.currentScene.rois[idx].label = this.editingName.trim();
                await this.saveScenes();
                this.renderROIs();
            }
            this.editingROIIdx = null;
            this.editingName = '';
        },
        
        cancelRenameROI() {
            this.editingROIIdx = null;
            this.editingName = '';
        },
        
        toggleROIMenu(idx) {
            if (this.openROIMenu === idx) {
                this.openROIMenu = null;
            } else {
                this.openROIMenu = idx;
                this.openSceneMenu = null;  // Close scene menu if open
            }
        },
        
        // ==================================================================
        // ROI EDITING (DRAG & RESIZE)
        // ==================================================================
        
        getROIAtPoint(x, y) {
            if (!this.currentScene || !this.currentScene.rois) return null;
            
            const handleSize = 10; // Size of resize handles
            
            // Check in reverse order (top ROI first)
            for (let i = this.currentScene.rois.length - 1; i >= 0; i--) {
                const roi = this.currentScene.rois[i];
                
                // Check resize handles (only for selected ROI)
                if (this.selectedROIIdx === i) {
                    // Top-left
                    if (Math.abs(x - roi.x) <= handleSize && Math.abs(y - roi.y) <= handleSize) {
                        return { roiIdx: i, handle: 'tl' };
                    }
                    // Top-right
                    if (Math.abs(x - (roi.x + roi.width)) <= handleSize && Math.abs(y - roi.y) <= handleSize) {
                        return { roiIdx: i, handle: 'tr' };
                    }
                    // Bottom-left
                    if (Math.abs(x - roi.x) <= handleSize && Math.abs(y - (roi.y + roi.height)) <= handleSize) {
                        return { roiIdx: i, handle: 'bl' };
                    }
                    // Bottom-right
                    if (Math.abs(x - (roi.x + roi.width)) <= handleSize && Math.abs(y - (roi.y + roi.height)) <= handleSize) {
                        return { roiIdx: i, handle: 'br' };
                    }
                }
                
                // Check if inside ROI body
                if (x >= roi.x && x <= roi.x + roi.width && y >= roi.y && y <= roi.y + roi.height) {
                    return { roiIdx: i, handle: 'body' };
                }
            }
            
            return null;
        },
        
        updateHoverState(x, y) {
            const hit = this.getROIAtPoint(x, y);
            const canvas = this.$refs.roiCanvas;
            if (!canvas) return;
            
            if (hit) {
                this.hoverROIIdx = hit.roiIdx;
                this.hoverHandle = hit.handle;
                
                // Update cursor based on handle
                if (hit.handle === 'tl' || hit.handle === 'br') {
                    canvas.style.cursor = 'nwse-resize';
                } else if (hit.handle === 'tr' || hit.handle === 'bl') {
                    canvas.style.cursor = 'nesw-resize';
                } else if (hit.handle === 'body') {
                    canvas.style.cursor = 'move';
                }
            } else {
                this.hoverROIIdx = null;
                this.hoverHandle = null;
                canvas.style.cursor = 'crosshair';
            }
        },
        
        startEditROI(roiHit, mouseX, mouseY) {
            this.editingROI = true;
            this.editROIIdx = roiHit.roiIdx;
            this.resizeHandle = roiHit.handle;
            this.dragStartX = mouseX;
            this.dragStartY = mouseY;
            
            // Store original ROI state
            const roi = this.currentScene.rois[roiHit.roiIdx];
            this.originalROI = {
                x: roi.x,
                y: roi.y,
                width: roi.width,
                height: roi.height
            };
            
            // Select this ROI
            this.selectROI(roiHit.roiIdx);
        },
        
        editingROIMove(mouseX, mouseY) {
            if (!this.editingROI || this.editROIIdx === null) return;
            
            const roi = this.currentScene.rois[this.editROIIdx];
            const deltaX = mouseX - this.dragStartX;
            const deltaY = mouseY - this.dragStartY;
            
            const canvas = this.$refs.roiCanvas;
            const maxX = canvas.width;
            const maxY = canvas.height;
            
            if (this.resizeHandle === 'body') {
                // Drag entire ROI
                roi.x = Math.max(0, Math.min(maxX - roi.width, this.originalROI.x + deltaX));
                roi.y = Math.max(0, Math.min(maxY - roi.height, this.originalROI.y + deltaY));
            } else if (this.resizeHandle === 'tl') {
                // Resize from top-left
                const newX = Math.max(0, Math.min(this.originalROI.x + this.originalROI.width - 20, this.originalROI.x + deltaX));
                const newY = Math.max(0, Math.min(this.originalROI.y + this.originalROI.height - 20, this.originalROI.y + deltaY));
                roi.width = this.originalROI.width + (this.originalROI.x - newX);
                roi.height = this.originalROI.height + (this.originalROI.y - newY);
                roi.x = newX;
                roi.y = newY;
            } else if (this.resizeHandle === 'tr') {
                // Resize from top-right
                const newY = Math.max(0, Math.min(this.originalROI.y + this.originalROI.height - 20, this.originalROI.y + deltaY));
                roi.width = Math.max(20, Math.min(maxX - this.originalROI.x, this.originalROI.width + deltaX));
                roi.height = this.originalROI.height + (this.originalROI.y - newY);
                roi.y = newY;
            } else if (this.resizeHandle === 'bl') {
                // Resize from bottom-left
                const newX = Math.max(0, Math.min(this.originalROI.x + this.originalROI.width - 20, this.originalROI.x + deltaX));
                roi.width = this.originalROI.width + (this.originalROI.x - newX);
                roi.height = Math.max(20, Math.min(maxY - this.originalROI.y, this.originalROI.height + deltaY));
                roi.x = newX;
            } else if (this.resizeHandle === 'br') {
                // Resize from bottom-right
                roi.width = Math.max(20, Math.min(maxX - this.originalROI.x, this.originalROI.width + deltaX));
                roi.height = Math.max(20, Math.min(maxY - this.originalROI.y, this.originalROI.height + deltaY));
            }
            
            // Round to integers
            roi.x = Math.round(roi.x);
            roi.y = Math.round(roi.y);
            roi.width = Math.round(roi.width);
            roi.height = Math.round(roi.height);
            
            // Redraw
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.renderROIs();
        },
        
        async endEditROI() {
            if (!this.editingROI) return;
            
            this.editingROI = false;
            
            // Save changes to history
            await this.saveScenes();
            
            // Reset edit state
            this.editROIIdx = null;
            this.resizeHandle = null;
            this.originalROI = null;
            this.dragStartX = 0;
            this.dragStartY = 0;
        },
        
        renderROIs() {
            const canvas = this.$refs.roiCanvas;
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Don't render ROI boxes during recording (keep them hidden from video)
            if (this.recording) {
                return;
            }
            
            // Find scene for current frame
            let activeScene = null;
            for (const scene of this.scenes) {
                if (scene.start_frame <= this.currentFrame && this.currentFrame <= scene.end_frame) {
                    activeScene = scene;
                    break;
                }
            }
            
            if (!activeScene || !activeScene.rois) return;
            
            // Draw ROIs only for active scene
            activeScene.rois.forEach((roi, idx) => {
                const isSelected = (activeScene === this.currentScene && idx === this.selectedROIIdx);
                const isHovered = (activeScene === this.currentScene && idx === this.hoverROIIdx);
                const color = roi.color_tag || '#61AFEF';
                
                // Fill with 30% opacity on hover, 20% otherwise
                ctx.fillStyle = this.hexToRgba(color, isHovered ? 0.3 : 0.2);
                ctx.fillRect(roi.x, roi.y, roi.width, roi.height);
                
                // Stroke with solid color
                ctx.strokeStyle = isSelected ? '#98C379' : color;
                ctx.lineWidth = isSelected ? 3 : 2;
                ctx.strokeRect(roi.x, roi.y, roi.width, roi.height);
                
                // Draw label background
                ctx.font = '14px "Segoe UI", sans-serif';
                const labelWidth = ctx.measureText(roi.label).width + 16;
                ctx.fillStyle = color;
                ctx.fillRect(roi.x, roi.y - 24, labelWidth, 24);
                
                // Draw label text
                ctx.fillStyle = '#FFFFFF';
                ctx.fillText(roi.label, roi.x + 8, roi.y - 7);
                
                // Draw resize handles for selected ROI
                if (isSelected) {
                    const handleSize = 10;
                    ctx.fillStyle = '#FFFFFF';
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 2;
                    
                    // Helper to draw handle
                    const drawHandle = (x, y) => {
                        ctx.fillRect(x - handleSize/2, y - handleSize/2, handleSize, handleSize);
                        ctx.strokeRect(x - handleSize/2, y - handleSize/2, handleSize, handleSize);
                    };
                    
                    // Top-left
                    drawHandle(roi.x, roi.y);
                    // Top-right
                    drawHandle(roi.x + roi.width, roi.y);
                    // Bottom-left
                    drawHandle(roi.x, roi.y + roi.height);
                    // Bottom-right
                    drawHandle(roi.x + roi.width, roi.y + roi.height);
                }
            });
        },
        
        hexToRgba(hex, alpha) {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        },

        // ==================================================================
        // RECORDING PROGRESS MODAL HELPERS
        // ==================================================================

        resetProgressModal() {
            // Close other modals before showing progress
            this.showNewVideoModal = false;
            this.showRecordModal = false;
            this.showProcessModal = false;
            this.showROIModal = false;

            this.progressSteps = [
                { key: 'stop', label: 'Stopping recording', status: 'pending' },
                { key: 'heatmaps', label: 'Generating heatmaps', status: 'pending' },
                { key: 'stats', label: 'Calculating ROI statistics', status: 'pending' },
                { key: 'overlay', label: 'Building overlay video', status: 'pending' }
            ];
            this.progressMessage = 'Finalizing recording...';
            this.progressError = null;
            this.progressComplete = false;
            this.showProgressModal = true;
        },

        updateProgressStatus(key, status) {
            const step = this.progressSteps.find(s => s.key === key);
            if (step) {
                step.status = status;
            }
        },

        progressStatusLabel(status) {
            if (status === 'success') return 'Done';
            if (status === 'active') return 'In progress';
            if (status === 'error') return 'Error';
            return 'Pending';
        },

        closeProgressModal() {
            if (this.processing && !this.progressComplete && !this.progressError) return;
            this.showProgressModal = false;
        },

        async runPostProcessingPipeline() {
            this.processing = true;
            this.progressMessage = 'Running post-processing...';
            let currentKey = null;
            try {
                const steps = [
                    { key: 'detection', label: 'Detecting gaze from recording', action: () => axios.post('/api/processing/start-post-processing') },
                    { key: 'heatmaps', label: 'Generating heatmaps', action: () => axios.post('/api/processing/generate-heatmaps') },
                    { key: 'stats', label: 'Calculating ROI statistics', action: () => axios.post('/api/processing/roi-statistics') },
                    { key: 'overlay', label: 'Building overlay video', action: () => axios.post('/api/processing/overlay-video') }
                ];

                for (const step of steps) {
                    currentKey = step.key;
                    this.updateProgressStatus(step.key, 'active');
                    this.processingStatus = step.label;
                    this.progressMessage = step.label;
                    await step.action();
                    this.updateProgressStatus(step.key, 'success');
                }

                this.processingStatus = '';
                this.progressMessage = 'All processing complete.';
                this.progressComplete = true;
                this.statusMessage = 'Recording complete!';
            } catch (error) {
                const message = error.response?.data?.error || error.message;
                if (currentKey) {
                    this.updateProgressStatus(currentKey, 'error');
                }
                this.progressError = message;
                this.progressMessage = 'Processing failed';
                this.statusMessage = 'Processing failed';
                throw error;
            } finally {
                this.processing = false;
            }
        },
        
        // ==================================================================
        // RECORDING
        // ==================================================================
        
        findROIAtPosition(x, y) {
            if (!this.currentScene || !this.currentScene.rois) return null;
            
            for (const roi of this.currentScene.rois) {
                if (x >= roi.x && x <= roi.x + roi.width &&
                    y >= roi.y && y <= roi.y + roi.height) {
                    return roi;
                }
            }
            return null;
        },
        
        async openRecordModal() {
            // Check device status before opening modal
            try {
                const response = await axios.get('/api/recording/check-devices');
                this.useMouseFallback = response.data.use_mouse_fallback || false;
                this.showRecordModal = true;
            } catch (error) {
                // If check fails, assume mouse fallback
                console.warn('Device check failed, assuming mouse fallback:', error);
                this.useMouseFallback = true;
                this.showRecordModal = true;
            }
        },
        
        async startRecording() {
            if (!this.videoInfo) {
                alert('Please load a video first');
                return;
            }

            if (this.showProgressModal && !this.progressComplete && !this.progressError) {
                alert('Please wait until current processing finishes.');
                return;
            }
            
            try {
                const response = await axios.post('/api/recording/start', {
                    participant_name: 'Participant'
                }, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                // Recording started successfully
                this.recording = true;
                this.framesRecorded = 0;
                this.sessionDir = response.data.session_dir;
                this.useMouseFallback = response.data.use_mouse_fallback || false;
                
                // Update status message based on recording mode
                if (this.useMouseFallback) {
                    this.statusMessage = 'Recording: MOUSE TRACKING';
                    console.log('✓ Mouse tracking mode active');
                } else {
                    this.statusMessage = 'Recording: EYE TRACKING (OBS)';
                    console.log('✓ OBS eye tracking mode active');
                }
                
                // Reset video to start
                const video = this.$refs.videoPlayer;
                video.currentTime = 0;
                this.currentFrame = 0;
                
                // Try to enter fullscreen (optional - don't block if it fails)
                try {
                    const wrapper = video.parentElement;
                    if (wrapper.requestFullscreen) {
                        await wrapper.requestFullscreen();
                    } else if (wrapper.webkitRequestFullscreen) {
                        await wrapper.webkitRequestFullscreen();
                    } else if (wrapper.msRequestFullscreen) {
                        await wrapper.msRequestFullscreen();
                    }
                } catch (fullscreenError) {
                    // Fullscreen not available or blocked - continue anyway
                    console.log('Fullscreen not available, continuing with normal view');
                }
                
                // Pause and show overlay
                video.pause();
                this.playing = false;
                this.showRecordingOverlay = true;
                
            } catch (error) {
                console.error('Recording start error:', error);
                const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
                alert('Failed to start recording: ' + errorMsg);
            }
        },
        
        async startPlaybackAndRecording() {
            // Hide overlay and start playback
            this.showRecordingOverlay = false;
            this.statusMessage = 'Recording...';
            
            const video = this.$refs.videoPlayer;
            video.play();
            this.playing = true;

            // Hide cursor during recording playback
            document.body.classList.add('recording-cursor-hidden');
            
            // Start per-frame recording loop
            this.lastRecordedFrame = -1;
            this.framesRecorded = 0;
            this.recordingFrameLoop();
        },
        
        async autoStopRecording() {
            if (!this.recording) return;
            
            // Stop video
            const video = this.$refs.videoPlayer;
            video.pause();
            this.playing = false;

            // Restore cursor visibility
            document.body.classList.remove('recording-cursor-hidden');
            
            // Stop recording loop
            if (this.recordingAnimationId) {
                cancelAnimationFrame(this.recordingAnimationId);
                this.recordingAnimationId = null;
            }
            
            // Exit fullscreen
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else if (document.webkitFullscreenElement) {
                document.webkitExitFullscreen();
            } else if (document.msFullscreenElement) {
                document.msExitFullscreen();
            }
            
            // Stop recording
            this.resetProgressModal();
            this.updateProgressStatus('stop', 'active');

            try {
                const response = await axios.post('/api/recording/stop', {}, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                this.updateProgressStatus('stop', 'success');
                this.recording = false;
                this.statusMessage = 'Processing...';
                this.sessionDir = response.data.session_dir;
                this.framesRecorded = response.data.frames_recorded;
            } catch (error) {
                const message = error.response?.data?.error || error.message;
                this.updateProgressStatus('stop', 'error');
                this.progressError = message;
                alert('Failed to stop recording: ' + message);
                this.recording = false;
                this.processing = false;
                return;
            }

            try {
                await this.runPostProcessingPipeline();
                this.progressMessage = 'Recording complete!';
                alert(`Recording complete!\n\nFrames: ${this.framesRecorded}\nLocation: ${this.sessionDir}\n\nAll post-processing completed automatically.`);
            } catch (error) {
                const message = error.response?.data?.error || error.message;
                this.progressError = message;
                alert('Post-processing failed: ' + message);
            }
        },
        
        async stopRecording() {
            if (!this.recording) return;
            try {
                // Exit fullscreen if active
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                } else if (document.webkitFullscreenElement) {
                    document.webkitExitFullscreen();
                } else if (document.msFullscreenElement) {
                    document.msExitFullscreen();
                }

                // Stop playback
                const video = this.$refs.videoPlayer;
                video.pause();
                this.playing = false;

                // Restore cursor visibility
                document.body.classList.remove('recording-cursor-hidden');

                this.resetProgressModal();
                this.updateProgressStatus('stop', 'active');

                const response = await axios.post('/api/recording/stop', {}, {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                this.updateProgressStatus('stop', 'success');
                this.recording = false;
                this.statusMessage = 'Processing...';
                this.sessionDir = response.data.session_dir;
                this.framesRecorded = response.data.frames_recorded;

                await this.runPostProcessingPipeline();
                this.progressMessage = 'Recording complete!';
                alert(`Recording saved!\nFrames: ${response.data.frames_recorded}\nLocation: ${response.data.session_dir}\n\nPost-processing finished.`);
            } catch (error) {
                alert('Failed to stop recording: ' + error.message);
            }
        },
        
        // ==================================================================
        // POST-PROCESSING
        // ==================================================================
        
        async generateHeatmaps() {
            if (!this.sessionDir) {
                alert('No recording session found');
                return;
            }
            
            this.processing = true;
            this.processingStatus = 'Generating heatmaps...';
            
            try {
                const response = await axios.post('/api/processing/generate-heatmaps');
                this.processingStatus = `Generated ${response.data.heatmaps.length} heatmaps`;
                
                setTimeout(() => {
                    this.processingStatus = '';
                    this.processing = false;
                }, 3000);
            } catch (error) {
                alert('Failed to generate heatmaps: ' + error.message);
                this.processing = false;
                this.processingStatus = '';
            }
        },
        
        async generateROIStats() {
            if (!this.sessionDir) {
                alert('No recording session found');
                return;
            }
            
            this.processing = true;
            this.processingStatus = 'Generating ROI statistics...';
            
            try {
                const response = await axios.post('/api/processing/roi-statistics');
                this.processingStatus = `Statistics saved: ${response.data.file}`;
                
                setTimeout(() => {
                    this.processingStatus = '';
                    this.processing = false;
                }, 3000);
            } catch (error) {
                alert('Failed to generate statistics: ' + error.message);
                this.processing = false;
                this.processingStatus = '';
            }
        },
        
        async createOverlayVideo() {
            if (!this.sessionDir) {
                alert('No recording session found');
                return;
            }
            
            this.processing = true;
            this.processingStatus = 'Creating overlay video... (this may take a while)';
            
            try {
                const response = await axios.post('/api/processing/overlay-video');
                this.processingStatus = `Overlay video created: ${response.data.filename}`;
                
                setTimeout(() => {
                    this.processingStatus = '';
                    this.processing = false;
                }, 5000);
            } catch (error) {
                alert('Failed to create overlay video: ' + error.message);
                this.processing = false;
                this.processingStatus = '';
            }
        },
        
        async createOverlayHeatmapVideo() {
            if (!this.sessionDir) {
                alert('No recording session found');
                return;
            }
            
            this.processing = true;
            this.processingStatus = 'Creating heatmap overlay videos per scene... (this may take a while)';
            
            try {
                const response = await axios.post('/api/processing/overlay-heatmap-video');
                this.processingStatus = `Heatmap overlay videos created: ${response.data.videos.length} scene(s)`;
                
                setTimeout(() => {
                    this.processingStatus = '';
                    this.processing = false;
                }, 5000);
            } catch (error) {
                alert('Failed to create heatmap overlay videos: ' + error.message);
                this.processing = false;
                this.processingStatus = '';
            }
        },
        
        async processAll() {
            if (!this.sessionDir) {
                alert('No recording session found');
                return;
            }
            
            this.processing = true;
            
            try {
                // Generate heatmaps
                this.processingStatus = 'Generating heatmaps...';
                await axios.post('/api/processing/generate-heatmaps');
                
                // Generate ROI statistics
                this.processingStatus = 'Calculating ROI statistics...';
                await axios.post('/api/processing/roi-statistics');
                
                // Create overlay video
                this.processingStatus = 'Creating overlay video... (this may take a while)';
                await axios.post('/api/processing/overlay-video');
                
                // Create heatmap overlay videos
                this.processingStatus = 'Creating heatmap overlay videos per scene... (this may take a while)';
                await axios.post('/api/processing/overlay-heatmap-video');
                
                this.processingStatus = 'All processing complete!';
                alert('✅ All processing complete!\n\nGenerated:\n- Heatmaps\n- ROI Statistics\n- Overlay Video\n- Heatmap Overlay Videos (per scene)\n\nCheck the session folder.');
                
                setTimeout(() => {
                    this.processingStatus = '';
                    this.processing = false;
                }, 5000);
            } catch (error) {
                alert('Failed during processing: ' + error.message);
                this.processing = false;
                this.processingStatus = '';
            }
        },
        
        // ==================================================================
        // ROI ANALYSIS API HELPER
        // ==================================================================
        
        async analyzeROIFromVideo(videoPath, rois, gazeData = null, options = {}) {
            /**
             * Call the /api/process_roi endpoint to analyze ROI regions.
             * 
             * @param {string} videoPath - Path to the video file
             * @param {Array} rois - Array of ROI objects with {x, y, width, height, label}
             * @param {Array} gazeData - Optional array of gaze points {frame, x, y}
             * @param {Object} options - Optional settings
             * @returns {Promise} Response with per-frame statistics
             * 
             * Example usage:
             *   const result = await this.analyzeROIFromVideo(
             *       this.videoInfo.filename,
             *       this.currentScene.rois,
             *       this.importedGazeData,
             *       { start_frame: 0, end_frame: 100, analysis_type: 'both' }
             *   );
             */
            try {
                const payload = {
                    video_path: videoPath,
                    rois: rois,
                    gaze_data: gazeData,
                    start_frame: options.start_frame || 0,
                    end_frame: options.end_frame || null,
                    analysis_type: options.analysis_type || 'both'
                };
                
                const response = await axios.post('/api/process_roi', payload);
                
                if (response.data.success) {
                    console.log('ROI Analysis Summary:', response.data.summary);
                    console.log('Total frames processed:', response.data.frames.length);
                    return response.data;
                } else {
                    throw new Error(response.data.error || 'Analysis failed');
                }
            } catch (error) {
                console.error('ROI Analysis Error:', error);
                const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
                alert('Failed to analyze ROI: ' + errorMsg);
                throw error;
            }
        }
    }
}).mount('#app');
