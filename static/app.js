// Meeting Actions - Frontend JavaScript

class MeetingActionsApp {
    constructor() {
        this.transcriptId = null;
        this.analysisData = null;
        this.analysisId = null;
        this.selectedFile = null;
        this.init();
    }

    init() {
        console.log('App initialization started');
        console.log('HTML content check - fileInput element:', document.getElementById('fileInput'));
        console.log('HTML content check - uploadTab element:', document.getElementById('uploadTab'));
        console.log('HTML content check - uploadForm element:', document.getElementById('uploadForm'));
        
        this.bindEvents();
        this.initTabs();
        
        // Set today's date as default
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('meetingDate').value = today;
    }

    bindEvents() {
        // Transcript form
        document.getElementById('transcriptForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.ingestTranscript();
        });

        // Upload form
        const uploadForm = document.getElementById('uploadForm');
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => {
                e.preventDefault();
                console.log('Upload form submitted');
                console.log('Current active tab:', document.querySelector('.input-tab-btn.active').dataset.tab);
                console.log('Upload tab visible:', document.getElementById('uploadTab').classList.contains('active'));
                this.uploadAndTranscribe();
            });
        } else {
            console.error('Upload form not found');
        }

        // File input change
        const fileInput = document.getElementById('fileInput');
        console.log('Initializing file input event listener:', fileInput);
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                console.log('File input change event:', e.target.files[0]);
                this.handleFileSelect(e.target.files[0]);
            });
        } else {
            console.error('File input not found during initialization');
        }

        // Drag and drop
        this.setupDragAndDrop();

        // Analysis form
        document.getElementById('analysisForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.analyzeTranscript();
        });

        // Sync button
        document.getElementById('syncBtn').addEventListener('click', () => {
            this.syncToNotion();
        });

        // History buttons
        document.getElementById('loadTranscriptsBtn').addEventListener('click', () => {
            this.loadTranscriptHistory();
        });

        document.getElementById('loadAnalysesBtn').addEventListener('click', () => {
            this.loadAnalysisHistory();
        });
    }

    initTabs() {
        // Main analysis tabs
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;
                
                // Update active states
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                button.classList.add('active');
                document.getElementById(`${targetTab}Tab`).classList.add('active');
            });
        });

        // Input method tabs
        const inputTabButtons = document.querySelectorAll('.input-tab-btn');
        const inputTabContents = document.querySelectorAll('.input-tab-content');

        inputTabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;
                console.log('Tab clicked:', targetTab);
                
                // Update active states
                inputTabButtons.forEach(btn => btn.classList.remove('active'));
                inputTabContents.forEach(content => content.classList.remove('active'));
                
                button.classList.add('active');
                document.getElementById(`${targetTab}Tab`).classList.add('active');
                
                // Debug: Check if file input is accessible after tab switch
                if (targetTab === 'upload') {
                    setTimeout(() => {
                        const fileInput = document.getElementById('fileInput');
                        console.log('File input after tab switch:', fileInput);
                        console.log('Upload tab content:', document.getElementById('uploadTab'));
                    }, 100);
                }
            });
        });

        // History tabs
        const historyTabButtons = document.querySelectorAll('.history-tab-btn');
        const historyTabContents = document.querySelectorAll('.history-tab-content');

        historyTabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;
                
                // Update active states
                historyTabButtons.forEach(btn => btn.classList.remove('active'));
                historyTabContents.forEach(content => content.classList.remove('active'));
                
                button.classList.add('active');
                document.getElementById(`${targetTab}HistoryTab`).classList.add('active');
            });
        });
    }

    async ingestTranscript() {
        const transcript = document.getElementById('transcript').value.trim();
        const statusEl = document.getElementById('transcriptStatus');
        const submitBtn = document.querySelector('#transcriptForm button');

        if (!transcript) {
            this.showStatus(statusEl, 'Please enter a transcript', 'error');
            return;
        }

        this.showStatus(statusEl, 'Ingesting transcript...', 'loading');
        submitBtn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('transcript', transcript);

            const response = await fetch('/ingest', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.transcriptId = data.transcript_id;

            this.showStatus(statusEl, '✅ Transcript ingested successfully!', 'success');
            document.getElementById('analysisSection').style.display = 'block';
            
        } catch (error) {
            this.showStatus(statusEl, `❌ Error: ${error.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
        }
    }

    async analyzeTranscript() {
        const team = document.getElementById('team').value.trim();
        const product = document.getElementById('product').value.trim();
        const meetingDate = document.getElementById('meetingDate').value;
        const statusEl = document.getElementById('analysisStatus');
        const submitBtn = document.querySelector('#analysisForm button');

        if (!team || !product || !meetingDate) {
            this.showStatus(statusEl, 'Please fill in all fields', 'error');
            return;
        }

        this.showStatus(statusEl, '🤖 Analyzing transcript with Gemini...', 'loading');
        submitBtn.disabled = true;

        try {
            const params = new URLSearchParams({
                transcript_id: this.transcriptId,
                team: team,
                product: product,
                date: meetingDate
            });

            const response = await fetch(`/analyze?${params}`, {
                method: 'POST'
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            this.analysisData = await response.json();
            this.analysisId = this.analysisData.analysis_id;
            
            this.showStatus(statusEl, '✅ Analysis complete!', 'success');
            this.displayResults();
            document.getElementById('resultsSection').style.display = 'block';
            
        } catch (error) {
            this.showStatus(statusEl, `❌ Error: ${error.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
        }
    }

    displayResults() {
        this.displayDecisions();
        this.displayActions();
    }

    displayDecisions() {
        const container = document.getElementById('decisionsList');
        const decisions = this.analysisData.decisions || [];

        if (decisions.length === 0) {
            container.innerHTML = '<div class="empty-state">No decisions found in the transcript</div>';
            return;
        }

        container.innerHTML = decisions.map(decision => `
            <div class="item">
                <div class="item-title">${this.escapeHtml(decision.title)}</div>
                <div class="item-meta">
                    ${decision.owner ? `<span><strong>Owner:</strong> ${this.escapeHtml(decision.owner)}</span>` : ''}
                    ${decision.effective_date ? `<span><strong>Effective:</strong> ${decision.effective_date}</span>` : ''}
                    ${decision.rationale ? `<span><strong>Rationale:</strong> ${this.escapeHtml(decision.rationale)}</span>` : ''}
                </div>
            </div>
        `).join('');
    }

    displayActions() {
        const container = document.getElementById('actionsList');
        const actions = this.analysisData.actions || [];

        if (actions.length === 0) {
            container.innerHTML = '<div class="empty-state">No action items found in the transcript</div>';
            return;
        }

        container.innerHTML = actions.map(action => `
            <div class="item">
                <div class="item-title">${this.escapeHtml(action.title)}</div>
                <div class="item-meta">
                    ${action.assignee ? `<span><strong>Assignee:</strong> ${this.escapeHtml(action.assignee)}</span>` : ''}
                    ${action.due ? `<span><strong>Due:</strong> ${action.due}</span>` : ''}
                    ${action.priority ? `<span class="priority-${action.priority}"><strong>Priority:</strong> ${action.priority}</span>` : ''}
                    ${action.notes ? `<span><strong>Notes:</strong> ${this.escapeHtml(action.notes)}</span>` : ''}
                </div>
            </div>
        `).join('');
    }

    async syncToNotion() {
        const meetingUrl = document.getElementById('meetingUrl').value.trim();
        const statusEl = document.getElementById('syncStatus');
        const syncBtn = document.getElementById('syncBtn');

        if (!this.analysisData) {
            this.showStatus(statusEl, 'No analysis data to sync', 'error');
            return;
        }

        this.showStatus(statusEl, '🚀 Syncing to Notion...', 'loading');
        syncBtn.disabled = true;

        try {
            const response = await fetch('/notion/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    analysis: this.analysisData,
                    analysis_id: this.analysisId,
                    meeting_url: meetingUrl || null
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            const message = this.buildSyncMessage(result);
            this.showStatus(statusEl, `✅ ${message}`, 'success');
            
        } catch (error) {
            this.showStatus(statusEl, `❌ Sync failed: ${error.message}`, 'error');
        } finally {
            syncBtn.disabled = false;
        }
    }

    buildSyncMessage(result) {
        const parts = [];
        
        if (result.created) {
            const created = [];
            if (result.created.actions > 0) created.push(`${result.created.actions} action(s)`);
            if (result.created.decisions > 0) created.push(`${result.created.decisions} decision(s)`);
            if (created.length > 0) parts.push(`Created: ${created.join(', ')}`);
        }
        
        if (result.updated) {
            const updated = [];
            if (result.updated.actions > 0) updated.push(`${result.updated.actions} action(s)`);
            if (result.updated.decisions > 0) updated.push(`${result.updated.decisions} decision(s)`);
            if (updated.length > 0) parts.push(`Updated: ${updated.join(', ')}`);
        }
        
        if (result.errors && result.errors.length > 0) {
            parts.push(`Errors: ${result.errors.length}`);
            // Log detailed errors to console for debugging
            console.error('Notion sync errors:', result.errors);
            
            // Show first error in UI for debugging
            if (result.errors.length > 0) {
                parts.push(`First error: ${result.errors[0].substring(0, 100)}...`);
            }
        }
        
        return parts.length > 0 ? parts.join(' | ') : 'Sync completed';
    }

    showStatus(element, message, type) {
        element.textContent = message;
        element.className = `status ${type}`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async loadTranscriptHistory() {
        const container = document.getElementById('transcriptsList');
        const btn = document.getElementById('loadTranscriptsBtn');
        
        btn.disabled = true;
        container.innerHTML = '<div class="history-loading">Loading recent transcripts...</div>';

        try {
            const response = await fetch('/history/transcripts?limit=10');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            const transcripts = data.transcripts || [];

            if (transcripts.length === 0) {
                container.innerHTML = '<div class="empty-state">No recent transcripts found</div>';
                return;
            }

            container.innerHTML = transcripts.map(transcript => {
                const date = new Date(transcript.created_at).toLocaleDateString();
                const preview = transcript.content_preview || transcript.content.substring(0, 200) + '...';
                
                return `
                    <div class="history-item" data-transcript-id="${transcript.id}">
                        <div class="history-item-header">
                            <h4 class="history-item-title">Transcript ${transcript.id.substring(0, 8)}...</h4>
                            <span class="history-item-date">${date}</span>
                        </div>
                        <div class="history-item-preview">${this.escapeHtml(preview)}</div>
                        <div class="history-item-actions">
                            <button onclick="app.recoverTranscript('${transcript.id}')">🔄 Recover</button>
                            <button onclick="app.viewTranscript('${transcript.id}')">👁️ View</button>
                        </div>
                    </div>
                `;
            }).join('');

        } catch (error) {
            container.innerHTML = `<div class="empty-state">Failed to load transcripts: ${error.message}</div>`;
        } finally {
            btn.disabled = false;
        }
    }

    async loadAnalysisHistory() {
        const container = document.getElementById('analysesList');
        const btn = document.getElementById('loadAnalysesBtn');
        
        btn.disabled = true;
        container.innerHTML = '<div class="history-loading">Loading recent analyses...</div>';

        try {
            const response = await fetch('/history/analyses?limit=10');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            const analyses = data.analyses || [];

            if (analyses.length === 0) {
                container.innerHTML = '<div class="empty-state">No recent analyses found</div>';
                return;
            }

            container.innerHTML = analyses.map(analysis => {
                const date = new Date(analysis.created_at).toLocaleDateString();
                const decisionsCount = analysis.analysis_data.decisions?.length || 0;
                const actionsCount = analysis.analysis_data.actions?.length || 0;
                
                return `
                    <div class="history-item" data-analysis-id="${analysis.id}">
                        <div class="history-item-header">
                            <h4 class="history-item-title">${this.escapeHtml(analysis.team)} - ${this.escapeHtml(analysis.product)}</h4>
                            <span class="history-item-date">${date}</span>
                        </div>
                        <div class="history-item-meta">
                            <span>📋 ${decisionsCount} decisions</span>
                            <span>✅ ${actionsCount} actions</span>
                            <span>📅 ${analysis.meeting_date}</span>
                        </div>
                        <div class="history-item-actions">
                            <button onclick="app.recoverAnalysis('${analysis.id}')">🔄 Recover</button>
                            <button onclick="app.viewAnalysis('${analysis.id}')">👁️ View</button>
                            <button onclick="app.resyncAnalysis('${analysis.id}')">🚀 Re-sync</button>
                        </div>
                    </div>
                `;
            }).join('');

        } catch (error) {
            container.innerHTML = `<div class="empty-state">Failed to load analyses: ${error.message}</div>`;
        } finally {
            btn.disabled = false;
        }
    }

    async recoverTranscript(transcriptId) {
        try {
            const response = await fetch(`/recovery/transcript/${transcriptId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Populate transcript field
            document.getElementById('transcript').value = data.content;
            this.transcriptId = transcriptId;
            
            // Show success and enable analysis section
            document.getElementById('transcriptStatus').innerHTML = 
                '<div class="recovery-banner"><h3>🔄 Transcript Recovered!</h3><p>Your previous transcript has been restored. You can now analyze it again.</p></div>';
            document.getElementById('analysisSection').style.display = 'block';
            
            // If there's existing analysis, show that too
            if (data.has_analysis && data.analysis) {
                this.analysisData = data.analysis.analysis_data;
                this.analysisId = data.analysis.id;
                this.displayResults();
                document.getElementById('resultsSection').style.display = 'block';
                
                // Populate form fields
                document.getElementById('team').value = data.analysis.team;
                document.getElementById('product').value = data.analysis.product;
                document.getElementById('meetingDate').value = data.analysis.meeting_date;
            }
            
        } catch (error) {
            alert(`Failed to recover transcript: ${error.message}`);
        }
    }

    async recoverAnalysis(analysisId) {
        try {
            const response = await fetch(`/history/analyses?limit=50`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            const analysis = data.analyses.find(a => a.id === analysisId);
            
            if (!analysis) {
                throw new Error('Analysis not found');
            }
            
            // Restore everything
            this.transcriptId = analysis.transcript_id;
            this.analysisData = analysis.analysis_data;
            this.analysisId = analysis.id;
            
            // Populate all fields
            document.getElementById('transcript').value = analysis.transcript_content;
            document.getElementById('team').value = analysis.team;
            document.getElementById('product').value = analysis.product;
            document.getElementById('meetingDate').value = analysis.meeting_date;
            
            // Show all sections
            document.getElementById('analysisSection').style.display = 'block';
            document.getElementById('resultsSection').style.display = 'block';
            
            // Display results
            this.displayResults();
            
            // Show success banner
            document.getElementById('analysisStatus').innerHTML = 
                '<div class="recovery-banner"><h3>🔄 Full Session Recovered!</h3><p>Your transcript, analysis, and results have been restored. You can now sync to Notion if needed.</p></div>';
            
        } catch (error) {
            alert(`Failed to recover analysis: ${error.message}`);
        }
    }

    viewTranscript(transcriptId) {
        // Simple view - just recover it
        this.recoverTranscript(transcriptId);
    }

    viewAnalysis(analysisId) {
        // Simple view - just recover it  
        this.recoverAnalysis(analysisId);
    }

    async resyncAnalysis(analysisId) {
        try {
            // First recover the analysis
            await this.recoverAnalysis(analysisId);
            
            // Then trigger sync
            await this.syncToNotion();
            
        } catch (error) {
            alert(`Failed to re-sync analysis: ${error.message}`);
        }
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        // Drag and drop events
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });

        // Click to browse
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
    }

    handleFileSelect(file) {
        console.log('handleFileSelect called with:', file);
        if (!file) return;
        
        // Store the file for later use
        this.selectedFile = file;

        // Validate file type
        const validTypes = ['audio/', 'video/'];
        const isValidType = validTypes.some(type => file.type.startsWith(type));
        
        if (!isValidType) {
            alert('Please select an audio or video file.');
            return;
        }

        // Validate file size (25MB limit)
        const maxSize = 25 * 1024 * 1024; // 25MB in bytes
        if (file.size > maxSize) {
            alert('File size must be less than 25MB.');
            return;
        }

        // Show file info
        this.showFileInfo(file);
        
        // Enable upload button
        document.getElementById('uploadBtn').disabled = false;
    }

    showFileInfo(file) {
        const uploadArea = document.getElementById('uploadArea');
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        
        uploadArea.innerHTML = `
            <div class="file-info">
                <div class="file-info-icon">${this.getFileIcon(file.type)}</div>
                <div class="file-info-details">
                    <h4>${file.name}</h4>
                    <p>${fileSizeMB} MB • ${file.type}</p>
                </div>
            </div>
        `;
    }

    getFileIcon(mimeType) {
        if (mimeType.startsWith('audio/')) return '🎵';
        if (mimeType.startsWith('video/')) return '🎬';
        return '📁';
    }

    async uploadAndTranscribe() {
        console.log('uploadAndTranscribe called');
        console.log('Selected file from storage:', this.selectedFile);
        
        const fileInput = document.getElementById('fileInput');
        const language = document.getElementById('language').value;
        const statusEl = document.getElementById('transcriptStatus');
        const uploadBtn = document.getElementById('uploadBtn');

        console.log('File input element:', fileInput);
        console.log('File input files:', fileInput?.files);
        console.log('All elements with fileInput ID:', document.querySelectorAll('#fileInput'));

        // Use stored file directly since we know it exists
        const file = this.selectedFile;
        
        // We don't need to find the file input element since we have the file stored
        console.log('Using stored file for upload:', file.name, file.size);
        
        if (!file) {
            this.showStatus(statusEl, 'Please select a file first', 'error');
            return;
        }
        this.showStatus(statusEl, '🎤 Processing audio/video file... This may take a few minutes.', 'loading');
        uploadBtn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('file', file);
            if (language) {
                formData.append('language', language);
            }

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Store transcript ID and populate textarea
            this.transcriptId = data.transcript_id;
            document.getElementById('transcript').value = data.transcript;
            
            this.showStatus(statusEl, `✅ File processed! (${data.file_size_mb}MB file)`, 'success');
            document.getElementById('analysisSection').style.display = 'block';
            
            // Switch back to transcript tab to show the result
            document.querySelector('[data-tab="transcript"]').click();
            
        } catch (error) {
            this.showStatus(statusEl, `❌ Transcription failed: ${error.message}`, 'error');
        } finally {
            uploadBtn.disabled = false;
        }
    }
}

// Initialize the app when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new MeetingActionsApp();
});
