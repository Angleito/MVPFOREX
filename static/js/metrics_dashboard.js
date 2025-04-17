document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    createPatternRecognitionChart();
    createNLPMetricsChart();
    createLatencyChart();
    createBacktestChart();
    createFeedbackChart();
});

function createPatternRecognitionChart() {
    const data = [{
        values: [85, 15],
        labels: ['Accurate', 'Inaccurate'],
        type: 'pie',
        name: 'Pattern Recognition Accuracy'
    }];

    const layout = {
        height: 300,
        showlegend: true
    };

    Plotly.newPlot('patternRecognitionChart', data, layout);
}

function createNLPMetricsChart() {
    const data = [{
        x: ['BLEU', 'ROUGE', 'METEOR'],
        y: [0.75, 0.82, 0.78],
        type: 'bar',
        name: 'NLP Metrics'
    }];

    const layout = {
        height: 300,
        yaxis: {
            range: [0, 1],
            title: 'Score'
        }
    };

    Plotly.newPlot('nlpMetricsChart', data, layout);
}

function createLatencyChart() {
    const data = [{
        y: [150, 180, 120, 200, 160],
        type: 'box',
        name: 'API Response Times (ms)'
    }];

    const layout = {
        height: 300,
        yaxis: {
            title: 'Milliseconds'
        }
    };

    Plotly.newPlot('latencyChart', data, layout);
}

function createBacktestChart() {
    const data = [{
        x: ['Win Rate', 'Profit Factor', 'Sharpe Ratio', 'Max Drawdown'],
        y: [0.65, 1.8, 1.2, 0.15],
        type: 'bar',
        name: 'Backtest Metrics'
    }];

    const layout = {
        height: 300,
        yaxis: {
            title: 'Value'
        }
    };

    Plotly.newPlot('backtestChart', data, layout);
}

function createFeedbackChart() {
    const data = [{
        values: [45, 30, 15, 7, 3],
        labels: ['5 Stars', '4 Stars', '3 Stars', '2 Stars', '1 Star'],
        type: 'pie',
        name: 'User Feedback Distribution'
    }];

    const layout = {
        height: 300,
        showlegend: true
    };

    Plotly.newPlot('feedbackChart', data, layout);
}

// Function to update metrics with new data
function updateMetrics(data) {
    if (data.patternRecognition) {
        Plotly.update('patternRecognitionChart', 
            {'values': [data.patternRecognition.accurate, data.patternRecognition.inaccurate]});
    }
    
    if (data.nlpMetrics) {
        Plotly.update('nlpMetricsChart', 
            {'y': [[data.nlpMetrics.bleu, data.nlpMetrics.rouge, data.nlpMetrics.meteor]]});
    }
    
    if (data.latency) {
        Plotly.update('latencyChart', {'y': [data.latency]});
    }
    
    if (data.backtest) {
        Plotly.update('backtestChart', 
            {'y': [[data.backtest.winRate, data.backtest.profitFactor, 
                   data.backtest.sharpeRatio, data.backtest.maxDrawdown]]});
    }
    
    if (data.feedback) {
        Plotly.update('feedbackChart', {'values': [
            data.feedback.fiveStars,
            data.feedback.fourStars,
            data.feedback.threeStars,
            data.feedback.twoStars,
            data.feedback.oneStar
        ]});
    }
}