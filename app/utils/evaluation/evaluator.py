"""
Evaluation coordinator for benchmarking LLM models.

This module coordinates the evaluation process for different LLM models,
applying various metrics and storing the results.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import numpy as np

from app.utils.evaluation.metrics import (
    PatternRecognitionMetrics, 
    ExplanationQualityMetrics,
    ImageCaptioningMetrics,
    LatencyMetrics,
    BacktestMetrics
)

class LLMEvaluator:
    """Evaluator class for benchmarking LLM models."""
    
    def __init__(self, models: List[str], results_dir: str = "results/evaluation"):
        """Initialize the evaluator.
        
        Args:
            models: List of model names to evaluate
            results_dir: Directory to store evaluation results
        """
        self.models = models
        self.results_dir = results_dir
        self.results = {model: {} for model in models}
        
        # Create results directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)
    
    def evaluate_pattern_recognition(self, 
                                    model_predictions: Dict[str, List[str]], 
                                    ground_truth: List[str]) -> Dict[str, Dict[str, float]]:
        """Evaluate pattern recognition performance for each model.
        
        Args:
            model_predictions: Dictionary mapping model names to lists of predicted patterns
            ground_truth: List of actual patterns (ground truth)
            
        Returns:
            Dictionary with evaluation results for each model
        """
        results = {}
        
        for model in self.models:
            if model not in model_predictions:
                continue
                
            predictions = model_predictions[model]
            
            # Calculate accuracy
            accuracy = PatternRecognitionMetrics.accuracy(predictions, ground_truth)
            
            # Calculate precision, recall, and F1
            prf = PatternRecognitionMetrics.precision_recall_f1(predictions, ground_truth)
            
            results[model] = {
                "accuracy": accuracy,
                **prf
            }
            
            # Store results
            self.results[model]["pattern_recognition"] = results[model]
            
        return results
    
    def evaluate_explanation_quality(self, 
                                    model_explanations: Dict[str, str], 
                                    reference_explanations: List[str]) -> Dict[str, Dict[str, float]]:
        """Evaluate explanation quality for each model.
        
        Args:
            model_explanations: Dictionary mapping model names to explanations
            reference_explanations: List of reference explanations
            
        Returns:
            Dictionary with evaluation results for each model
        """
        results = {}
        
        for model in self.models:
            if model not in model_explanations:
                continue
                
            explanation = model_explanations[model]
            
            # Calculate BLEU score
            bleu = ExplanationQualityMetrics.bleu_score(explanation, reference_explanations)
            
            # Calculate ROUGE score (using the first reference)
            rouge = ExplanationQualityMetrics.rouge_score(explanation, reference_explanations[0])
            
            # Calculate METEOR score (using the first reference)
            meteor = ExplanationQualityMetrics.meteor_score(explanation, reference_explanations[0])
            
            results[model] = {
                "bleu": bleu,
                "rouge": rouge,
                "meteor": meteor
            }
            
            # Store results
            self.results[model]["explanation_quality"] = results[model]
            
        return results
    
    def evaluate_image_captioning(self, 
                                model_captions: Dict[str, str], 
                                reference_captions: List[str]) -> Dict[str, Dict[str, float]]:
        """Evaluate image captioning quality for each model.
        
        Args:
            model_captions: Dictionary mapping model names to captions
            reference_captions: List of reference captions
            
        Returns:
            Dictionary with evaluation results for each model
        """
        results = {}
        
        for model in self.models:
            if model not in model_captions:
                continue
                
            caption = model_captions[model]
            
            # Calculate CIDEr score
            cider = ImageCaptioningMetrics.cider_score(caption, reference_captions)
            
            results[model] = {
                "cider": cider
            }
            
            # Store results
            self.results[model]["image_captioning"] = results[model]
            
        return results
    
    def evaluate_latency(self, 
                        model_latencies: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """Evaluate latency performance for each model.
        
        Args:
            model_latencies: Dictionary mapping model names to lists of latency measurements
            
        Returns:
            Dictionary with evaluation results for each model
        """
        results = {}
        
        for model in self.models:
            if model not in model_latencies:
                continue
                
            latencies = model_latencies[model]
            
            # Calculate latency statistics
            latency_stats = LatencyMetrics.calculate_latency_stats(latencies)
            
            results[model] = latency_stats
            
            # Store results
            self.results[model]["latency"] = results[model]
            
        return results
    
    def evaluate_backtest(self, 
                        model_positions: Dict[str, List[int]], 
                        prices: List[float]) -> Dict[str, Dict[str, float]]:
        """Evaluate backtest performance for each model.
        
        Args:
            model_positions: Dictionary mapping model names to lists of positions (-1, 0, 1)
            prices: List of prices
            
        Returns:
            Dictionary with evaluation results for each model
        """
        results = {}
        
        for model in self.models:
            if model not in model_positions:
                continue
                
            positions = model_positions[model]
            
            # Calculate returns
            returns = BacktestMetrics.calculate_returns(prices, positions)
            
            # Calculate Sharpe ratio
            sharpe = BacktestMetrics.sharpe_ratio(returns)
            
            # Calculate maximum drawdown
            max_dd = BacktestMetrics.maximum_drawdown(returns)
            
            # Calculate win rate
            # For this, we need to identify individual trades
            trades = []
            current_position = 0
            trade_return = 0.0
            
            for i, pos in enumerate(positions):
                if i == 0:
                    current_position = pos
                    continue
                    
                # If position changed, a trade was completed
                if pos != current_position and current_position != 0:
                    trades.append(trade_return)
                    trade_return = 0.0
                
                # Add return to current trade
                if current_position != 0:
                    price_return = (prices[i] / prices[i-1]) - 1.0
                    trade_return += price_return * current_position
                    
                current_position = pos
            
            # Add the last trade if there is one
            if trade_return != 0.0:
                trades.append(trade_return)
                
            # Calculate win rate
            win_rate = BacktestMetrics.win_rate(trades)
            
            # Calculate profit factor
            profit_factor = BacktestMetrics.profit_factor(trades)
            
            # Calculate total return
            total_return = np.prod(np.array(returns) + 1.0) - 1.0 if returns else 0.0
            
            results[model] = {
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "total_return": total_return,
                "num_trades": len(trades)
            }
            
            # Store results
            self.results[model]["backtest"] = results[model]
            
        return results
    
    def evaluate_user_feedback(self, 
                            model_feedback: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Incorporate user feedback into evaluation results.
        
        Args:
            model_feedback: Dictionary mapping model names to user feedback scores
            
        Returns:
            Dictionary with user feedback results for each model
        """
        results = {}
        
        for model in self.models:
            if model not in model_feedback:
                continue
                
            feedback = model_feedback[model]
            
            results[model] = feedback
            
            # Store results
            self.results[model]["user_feedback"] = results[model]
            
        return results
    
    def calculate_overall_scores(self, weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """Calculate overall scores for each model based on all metrics.
        
        Args:
            weights: Dictionary mapping metric categories to weights
                (default: equal weights for all categories)
            
        Returns:
            Dictionary mapping model names to overall scores
        """
        if weights is None:
            # Default weights
            categories = [
                "pattern_recognition", 
                "explanation_quality", 
                "image_captioning", 
                "latency", 
                "backtest", 
                "user_feedback"
            ]
            weights = {category: 1.0 / len(categories) for category in categories}
            
        overall_scores = {}
        
        for model in self.models:
            score = 0.0
            normalized_weight_sum = 0.0
            
            for category, weight in weights.items():
                if category not in self.results[model]:
                    continue
                    
                # Calculate category score based on the type of results
                category_results = self.results[model][category]
                
                if category == "pattern_recognition":
                    # Use F1 score as the category score
                    category_score = category_results.get("f1", 0.0)
                elif category == "explanation_quality":
                    # Average of BLEU, ROUGE-L F1, and METEOR
                    bleu = category_results.get("bleu", 0.0)
                    rouge_l = category_results.get("rouge", {}).get("rouge-l", {}).get("f", 0.0)
                    meteor = category_results.get("meteor", 0.0)
                    category_score = (bleu + rouge_l + meteor) / 3.0
                elif category == "image_captioning":
                    # Use CIDEr score
                    category_score = category_results.get("cider", 0.0)
                elif category == "latency":
                    # Use normalized inverse of mean latency (lower is better)
                    mean_latency = category_results.get("mean", 0.0)
                    if mean_latency > 0:
                        category_score = 1.0 / mean_latency
                    else:
                        category_score = 0.0
                elif category == "backtest":
                    # Use normalized Sharpe ratio
                    sharpe = category_results.get("sharpe_ratio", 0.0)
                    category_score = max(0.0, min(1.0, sharpe / 3.0))  # Normalize to [0, 1]
                elif category == "user_feedback":
                    # Average of user feedback scores
                    if category_results:
                        category_score = sum(category_results.values()) / len(category_results)
                    else:
                        category_score = 0.0
                else:
                    category_score = 0.0
                
                score += weight * category_score
                normalized_weight_sum += weight
            
            # Normalize score by weight sum
            if normalized_weight_sum > 0:
                score /= normalized_weight_sum
                
            overall_scores[model] = score
            
        # Store overall scores
        for model, score in overall_scores.items():
            self.results[model]["overall_score"] = score
            
        return overall_scores
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """Save evaluation results to a JSON file.
        
        Args:
            filename: Name of the file to save results to (default: auto-generated)
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            # Generate filename based on current date and time
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_results_{timestamp}.json"
            
        file_path = os.path.join(self.results_dir, filename)
        
        # Add metadata
        results_with_metadata = {
            "metadata": {
                "models": self.models,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            },
            "results": self.results
        }
        
        # Save results to file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(results_with_metadata, f, indent=2)
            
        return file_path
    
    def load_results(self, file_path: str) -> bool:
        """Load evaluation results from a JSON file.
        
        Args:
            file_path: Path to the JSON file to load results from
            
        Returns:
            True if results were loaded successfully, False otherwise
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                
            if "results" not in data:
                return False
                
            self.results = data["results"]
            
            # Update models list if metadata is available
            if "metadata" in data and "models" in data["metadata"]:
                self.models = data["metadata"]["models"]
                
            return True
        except Exception as e:
            print(f"Error loading results: {e}")
            return False
    
    def print_summary(self) -> str:
        """Generate a summary of evaluation results.
        
        Returns:
            Summary string
        """
        summary = "LLM Evaluation Summary\n"
        summary += "=" * 50 + "\n\n"
        
        # Get overall scores
        overall_scores = {model: self.results[model].get("overall_score", 0.0) for model in self.models}
        
        # Sort models by overall score
        sorted_models = sorted(self.models, key=lambda m: overall_scores.get(m, 0.0), reverse=True)
        
        # Print overall ranking
        summary += "Overall Ranking:\n"
        for i, model in enumerate(sorted_models):
            score = overall_scores.get(model, 0.0)
            summary += f"{i+1}. {model}: {score:.4f}\n"
        
        summary += "\n" + "=" * 50 + "\n\n"
        
        # Print detailed results for each category
        categories = [
            "pattern_recognition", 
            "explanation_quality", 
            "image_captioning", 
            "latency", 
            "backtest", 
            "user_feedback"
        ]
        
        for category in categories:
            summary += f"{category.replace('_', ' ').title()}:\n"
            summary += "-" * 30 + "\n"
            
            for model in sorted_models:
                if category in self.results[model]:
                    category_results = self.results[model][category]
                    
                    if isinstance(category_results, dict):
                        # Format each metric in the category
                        metrics_str = ", ".join(f"{k}: {v:.4f}" if isinstance(v, (int, float)) else f"{k}: {v}" 
                                            for k, v in category_results.items() 
                                            if not isinstance(v, dict))
                        summary += f"{model}: {metrics_str}\n"
                    else:
                        summary += f"{model}: {category_results}\n"
                else:
                    summary += f"{model}: No data\n"
                    
            summary += "\n"
            
        return summary