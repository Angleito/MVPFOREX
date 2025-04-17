class AnalysisHandler {
    constructor() {
        this.lastAnalysisData = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Attach click handlers to analyze buttons
        document.getElementById('analyzeBtn').addEventListener('click', () => this.analyze('/analyze'));
        document.getElementById('analyzeChatGPTBtn').addEventListener('click', () => this.analyze('/analyze/chatgpt41'));
        document.getElementById('analyzeClaudeBtn').addEventListener('click', () => this.analyze('/analyze/claude'));
        document.getElementById('analyzePerplexityBtn').addEventListener('click', () => this.analyze('/analyze/perplexity'));
        
        // Add export button handler
        document.getElementById('exportBtn').addEventListener('click', () => this.exportAnalysis());
    }

    async analyze(endpoint) {
        const loadingOverlay = document.getElementById('loading');
        const resultsDiv = document.getElementById('results');
        
        try {
            loadingOverlay.style.display = 'flex';
            resultsDiv.classList.add('d-none');
            
            // Get timeframe from chart handler
            const timeframe = window.chartHandler.timeframe;
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    instrument: 'XAU_USD',
                    granularity: timeframe
                })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();
            this.lastAnalysisData = data;
            
            if ((data.status === 'completed' || data.status === 'success') && data.data) {
                // Update market overview if data contains trend info
                if (data.data.trend_info) {
                    window.chartHandler.updateMarketOverview(data.data);
                }
                
                this.displayResults(data.data, endpoint);
            } else if (data.status === 'error') {
                throw new Error(data.error || 'Analysis failed');
            } else {
                throw new Error('Invalid response from server');
            }
        } catch (error) {
            console.error('Error in analysis:', error);
            resultsDiv.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger" role="alert">
                        <i class="bi bi-exclamation-triangle-fill"></i> Error in analysis: ${error.message}
                    </div>
                </div>
            `;
            resultsDiv.classList.remove('d-none');
        } finally {
            loadingOverlay.style.display = 'none';
        }
    }

    displayResults(data, endpoint) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '<h2 class="col-12 text-center mb-4">Analysis Results</h2>';
        
        // Handle individual model response format
        if (endpoint !== '/analyze') {
            this.displaySingleModelAnalysis(data, endpoint);
            return;
        }
        
        // Handle multi-model response format
        if (data && Object.keys(data).length > 0) {
            const models = Object.entries(data);
            
            // Create a row for each model's analysis
            models.forEach(([model, analysisData], index) => {
                const card = this.createAnalysisCard(model, analysisData);
                resultsDiv.appendChild(card);
                
                // After adding the card, initialize its feedback panel
                if (window.feedbackHandler) {
                    window.feedbackHandler.initializeFeedbackPanel(
                        `${model}-feedback`,
                        model,
                        analysisData.analysis
                    );
                }
            });
        } else {
            resultsDiv.innerHTML += `
                <div class="col-12">
                    <div class="alert alert-warning text-center" role="alert">
                        <i class="bi bi-info-circle-fill"></i> No analysis data available
                    </div>
                </div>
            `;
        }
        
        resultsDiv.classList.remove('d-none');
    }

    displaySingleModelAnalysis(data, endpoint) {
        const resultsDiv = document.getElementById('results');
        const modelMap = {
            '/analyze/chatgpt41': 'ChatGPT 4.1',
            '/analyze/claude': 'Claude 3.7',
            '/analyze/perplexity': 'Perplexity'
        };
        
        const modelName = modelMap[endpoint] || 'AI Model';
        const modelKey = endpoint.split('/').pop();
        
        const card = this.createAnalysisCard(modelKey, {
            analysis: data.analysis,
            model: data.model,
            elapsed_time: data.elapsed_time
        }, true);
        
        resultsDiv.appendChild(card);
        
        // Initialize feedback panel
        if (window.feedbackHandler) {
            window.feedbackHandler.initializeFeedbackPanel(
                `${modelKey}-feedback`,
                modelKey,
                data.analysis
            );
        }
        
        resultsDiv.classList.remove('d-none');
    }

    createAnalysisCard(model, analysisData, isFullWidth = false) {
        const colDiv = document.createElement('div');
        colDiv.className = isFullWidth ? 'col-12' : 'col-md-4 mb-4';
        
        const modelDisplayNames = {
            'gpt4': 'ChatGPT 4.1',
            'claude': 'Claude 3.7',
            'perplexity': 'Perplexity Pro',
            'chatgpt41': 'ChatGPT 4.1'
        };
        
        const modelName = modelDisplayNames[model] || model.toUpperCase();
        
        let cardContent;
        if (analysisData.error) {
            cardContent = `
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="card-title mb-0">${modelName}</h5>
                    </div>
                    <div class="card-body">
                        <p class="card-text text-danger">
                            <i class="bi bi-exclamation-circle-fill"></i> ${analysisData.error}
                        </p>
                    </div>
                </div>
            `;
        } else {
            const analysisText = analysisData.analysis || 'No analysis available';
            cardContent = `
                <div class="card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="card-title mb-0">${modelName}</h5>
                            <small class="text-muted">${analysisData.model || ''}</small>
                        </div>
                        ${analysisData.elapsed_time ? 
                            `<span class="badge bg-light text-dark">
                                <i class="bi bi-clock"></i> ${analysisData.elapsed_time.toFixed(1)}s
                            </span>` : 
                            ''}
                    </div>
                    <div class="card-body">
                        <p class="card-text">${analysisText.replace(/\n/g, '<br>')}</p>
                    </div>
                    <div class="card-footer bg-transparent" id="${model}-feedback">
                        <!-- Feedback panel will be initialized here -->
                    </div>
                </div>
            `;
        }
        
        colDiv.innerHTML = cardContent;
        return colDiv;
    }

    exportAnalysis() {
        if (!this.lastAnalysisData) {
            alert('No analysis data available to export');
            return;
        }

        const exportData = {
            timestamp: new Date().toISOString(),
            instrument: 'XAU_USD',
            timeframe: window.chartHandler.timeframe,
            analysis: this.lastAnalysisData
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `xauusd_analysis_${new Date().toISOString().slice(0,19).replace(/[-:]/g, '')}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}

// Initialize analysis handler when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.analysisHandler = new AnalysisHandler();
});