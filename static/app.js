// Meeting Actions - Frontend JavaScript

class MeetingActionsApp {
    constructor() {
        this.transcriptId = null;
        this.analysisData = null;
        this.init();
    }

    init() {
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

        // Analysis form
        document.getElementById('analysisForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.analyzeTranscript();
        });

        // Sync button
        document.getElementById('syncBtn').addEventListener('click', () => {
            this.syncToNotion();
        });
    }

    initTabs() {
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
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MeetingActionsApp();
});
