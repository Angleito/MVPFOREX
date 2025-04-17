"""
Dashboard module for visualizing model comparison metrics.
"""

import os
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
from datetime import datetime

class ModelComparisonDashboard:
    """Dashboard for visualizing model comparison metrics."""
    
    def __init__(self, results_dir: str = "results/dashboard"):
        """Initialize the dashboard.
        
        Args:
            results_dir: Directory to store dashboard results and visualizations
        """
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
        
    def create_metrics_table(self, data: Dict[str, Dict[str, Any]]) -> go.Figure:
        """Create an interactive table showing all metrics.
        
        Args:
            data: Dictionary with evaluation results for each model
            
        Returns:
            Plotly figure object
        """
        # Extract metrics for each model
        models = list(data.keys())
        metrics = []
        
        for model in models:
            model_data = data[model]
            metrics.append({
                "Model": model,
                "Chart Accuracy": f"{model_data['pattern_recognition']['accuracy']:.2%}",
                "BLEU Score": f"{model_data['explanation_quality']['bleu']:.3f}",
                "ROUGE-L": f"{model_data['explanation_quality']['rouge']['rouge-l']['f']:.3f}",
                "METEOR": f"{model_data['explanation_quality']['meteor']:.3f}",
                "Latency (s)": f"{model_data['latency']['mean']:.2f}",
                "Sharpe Ratio": f"{model_data['backtest']['sharpe_ratio']:.2f}",
                "Win Rate": f"{model_data['backtest']['win_rate']:.2%}",
                "Max Drawdown": f"{model_data['backtest']['max_drawdown']:.2%}"
            })
        
        df = pd.DataFrame(metrics)
        
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df.columns),
                fill_color='royalblue',
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=[df[col] for col in df.columns],
                fill_color='lavender',
                align='left'
            )
        )])
        
        fig.update_layout(
            title="Model Comparison Metrics",
            width=1000,
            height=400
        )
        
        return fig
    
    def create_radar_chart(self, data: Dict[str, Dict[str, Any]]) -> go.Figure:
        """Create a radar chart comparing model performance across key metrics.
        
        Args:
            data: Dictionary with evaluation results for each model
            
        Returns:
            Plotly figure object
        """
        models = list(data.keys())
        metrics = [
            "Pattern Recognition",
            "Explanation Quality",
            "Response Time",
            "Trading Performance"
        ]
        
        fig = go.Figure()
        
        for model in models:
            model_data = data[model]
            
            # Normalize metrics to [0,1] scale
            pattern_score = model_data['pattern_recognition']['f1']
            explanation_score = (
                model_data['explanation_quality']['bleu'] +
                model_data['explanation_quality']['rouge']['rouge-l']['f'] +
                model_data['explanation_quality']['meteor']
            ) / 3
            latency_score = 1 / (1 + model_data['latency']['mean'])  # Inverse for better visualization
            trading_score = max(0, min(1, model_data['backtest']['sharpe_ratio'] / 3))
            
            fig.add_trace(go.Scatterpolar(
                r=[pattern_score, explanation_score, latency_score, trading_score],
                theta=metrics,
                name=model,
                fill='toself'
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title="Model Performance Comparison",
            showlegend=True
        )
        
        return fig
    
    def create_backtest_chart(self, data: Dict[str, Dict[str, Any]]) -> go.Figure:
        """Create a bar chart comparing backtest metrics.
        
        Args:
            data: Dictionary with evaluation results for each model
            
        Returns:
            Plotly figure object
        """
        models = list(data.keys())
        metrics = ['sharpe_ratio', 'win_rate', 'profit_factor']
        
        backtest_data = []
        for model in models:
            for metric in metrics:
                backtest_data.append({
                    'Model': model,
                    'Metric': metric.replace('_', ' ').title(),
                    'Value': data[model]['backtest'][metric]
                })
        
        df = pd.DataFrame(backtest_data)
        
        fig = px.bar(
            df,
            x='Model',
            y='Value',
            color='Metric',
            barmode='group',
            title='Trading Performance Metrics'
        )
        
        return fig
    
    def generate_dashboard(self, data: Dict[str, Dict[str, Any]], output_dir: Optional[str] = None) -> str:
        """Generate a complete HTML dashboard.
        
        Args:
            data: Dictionary with evaluation results for each model
            output_dir: Optional directory to save the dashboard (default: self.results_dir)
            
        Returns:
            Path to the generated HTML file
        """
        if output_dir is None:
            output_dir = self.results_dir
            
        metrics_table = self.create_metrics_table(data)
        radar_chart = self.create_radar_chart(data)
        backtest_chart = self.create_backtest_chart(data)
        
        # Create dashboard HTML
        dashboard_html = f"""
        <html>
        <head>
            <title>Model Comparison Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{ padding: 20px; }}
                .chart-container {{ margin-bottom: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="mb-4">Model Comparison Dashboard</h1>
                <p class="text-muted">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="chart-container">
                    {metrics_table.to_html(include_plotlyjs=True, full_html=False)}
                </div>
                
                <div class="row">
                    <div class="col-md-6 chart-container">
                        {radar_chart.to_html(include_plotlyjs=False, full_html=False)}
                    </div>
                    <div class="col-md-6 chart-container">
                        {backtest_chart.to_html(include_plotlyjs=False, full_html=False)}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Save dashboard
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"dashboard_{timestamp}.html")
        
        with open(output_path, "w") as f:
            f.write(dashboard_html)
            
        return output_path