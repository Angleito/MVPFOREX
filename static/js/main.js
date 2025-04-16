document.addEventListener('DOMContentLoaded', (event) => {
    console.log("DOM fully loaded and parsed");

    const analyzeBtn = document.getElementById('analyze-btn');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');

    analyzeBtn.addEventListener('click', async () => {
        // Show loading state
        loadingDiv.classList.remove('d-none');
        resultsDiv.classList.add('d-none');
        analyzeBtn.disabled = true;

        try {
            const response = await fetch('/analyze');
            const data = await response.json();
            
            // Update the results section with the analysis from all models
            resultsDiv.innerHTML = `
                <div class="card mb-4">
                    <div class="card-header">
                        <h3>Market Information</h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h4>Trend Information</h4>
                                <p><strong>Direction:</strong> ${data.trend.direction}</p>
                                <p><strong>Strength:</strong> ${data.trend.strength}</p>
                                <p><strong>Current Price:</strong> $${data.trend.current_price}</p>
                            </div>
                            <div class="col-md-6">
                                <h4>Structure Points</h4>
                                <div class="mb-3">
                                    <h5>Swing Highs</h5>
                                    <ul class="list-unstyled">
                                        ${data.structure_points.swing_highs.map(h => 
                                            `<li>$${h.price} at ${new Date(h.time).toLocaleTimeString()}</li>`
                                        ).join('')}
                                    </ul>
                                </div>
                                <div>
                                    <h5>Swing Lows</h5>
                                    <ul class="list-unstyled">
                                        ${data.structure_points.swing_lows.map(l => 
                                            `<li>$${l.price} at ${new Date(l.time).toLocaleTimeString()}</li>`
                                        ).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <!-- GPT-4.1 Vision Analysis -->
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h4>GPT-4.1 Vision Analysis</h4>
                            </div>
                            <div class="card-body">
                                ${data.analyses.gpt4.error ? 
                                    `<div class="alert alert-danger">${data.analyses.gpt4.error}</div>` :
                                    `<pre class="analysis-text">${data.analyses.gpt4.analysis}</pre>`
                                }
                            </div>
                        </div>
                    </div>

                    <!-- Claude 3.7 Sonnet Analysis -->
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header bg-success text-white">
                                <h4>Claude 3.7 Sonnet Analysis</h4>
                            </div>
                            <div class="card-body">
                                ${data.analyses.claude.error ? 
                                    `<div class="alert alert-danger">${data.analyses.claude.error}</div>` :
                                    `<pre class="analysis-text">${data.analyses.claude.analysis}</pre>`
                                }
                            </div>
                        </div>
                    </div>

                    <!-- Perplexity Sonar Pro Analysis -->
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header bg-info text-white">
                                <h4>Perplexity Sonar Pro Analysis</h4>
                            </div>
                            <div class="card-body">
                                ${data.analyses.perplexity.error ? 
                                    `<div class="alert alert-danger">${data.analyses.perplexity.error}</div>` :
                                    `<pre class="analysis-text">${data.analyses.perplexity.analysis}</pre>`
                                }
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            resultsDiv.classList.remove('d-none');
        } catch (error) {
            console.error('Error:', error);
            resultsDiv.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    An error occurred while analyzing the market. Please try again.
                </div>
            `;
            resultsDiv.classList.remove('d-none');
        } finally {
            loadingDiv.classList.add('d-none');
            analyzeBtn.disabled = false;
        }
    });
});