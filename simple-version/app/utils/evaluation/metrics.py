"""
Metrics module for evaluating LLM performance in trading strategy analysis.

This module implements various metrics for evaluating LLM performance:
- Pattern recognition accuracy metrics (Accuracy, Precision, Recall, F1)
- NLP metrics for explanation quality (BLEU, ROUGE, METEOR)
- Image captioning metrics (CIDEr)
- Latency measurements
- Backtest metrics (Sharpe ratio, drawdown, etc.)
"""

import time
import numpy as np
from typing import Dict, List, Any, Union, Tuple
import json
import os

# Will need to install these packages
# from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
# from rouge import Rouge
# from nltk.translate.meteor_score import meteor_score

class PatternRecognitionMetrics:
    """Metrics for evaluating chart pattern recognition performance."""
    
    @staticmethod
    def accuracy(predictions: List[str], ground_truth: List[str]) -> float:
        """Calculate accuracy of pattern recognition.
        
        Args:
            predictions: List of predicted patterns
            ground_truth: List of actual patterns
            
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        if not predictions or not ground_truth or len(predictions) != len(ground_truth):
            return 0.0
            
        correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
        return correct / len(predictions)
    
    @staticmethod
    def precision_recall_f1(predictions: List[str], ground_truth: List[str]) -> Dict[str, float]:
        """Calculate precision, recall, and F1 score for pattern recognition.
        
        Args:
            predictions: List of predicted patterns
            ground_truth: List of actual patterns
            
        Returns:
            Dictionary with precision, recall, and F1 scores
        """
        if not predictions or not ground_truth:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
            
        # Get unique patterns
        unique_patterns = set(ground_truth + predictions)
        
        # Calculate per-class precision and recall
        metrics = {}
        for pattern in unique_patterns:
            # True positives: predicted as pattern and actually is pattern
            tp = sum(1 for p, g in zip(predictions, ground_truth) if p == pattern and g == pattern)
            
            # All predicted as this pattern
            predicted_as_pattern = sum(1 for p in predictions if p == pattern)
            
            # All actually this pattern
            actually_pattern = sum(1 for g in ground_truth if g == pattern)
            
            # Calculate precision and recall for this pattern
            precision = tp / predicted_as_pattern if predicted_as_pattern > 0 else 0.0
            recall = tp / actually_pattern if actually_pattern > 0 else 0.0
            
            # F1 score
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            metrics[pattern] = {"precision": precision, "recall": recall, "f1": f1}
        
        # Calculate macro average
        avg_precision = sum(m["precision"] for m in metrics.values()) / len(metrics)
        avg_recall = sum(m["recall"] for m in metrics.values()) / len(metrics)
        avg_f1 = sum(m["f1"] for m in metrics.values()) / len(metrics)
        
        return {
            "precision": avg_precision,
            "recall": avg_recall,
            "f1": avg_f1,
            "per_class": metrics
        }


class ExplanationQualityMetrics:
    """Metrics for evaluating the quality of explanations generated by LLMs."""
    
    @staticmethod
    def bleu_score(candidate: str, references: List[str]) -> float:
        """Calculate BLEU score for explanation quality.
        
        This is a placeholder. In a real implementation, you would use:
        from nltk.translate.bleu_score import sentence_bleu
        
        Args:
            candidate: Candidate explanation text
            references: List of reference explanation texts
            
        Returns:
            BLEU score (0.0 to 1.0)
        """
        # Placeholder implementation
        # In real implementation: return sentence_bleu([r.split() for r in references], candidate.split())
        return 0.7  # Placeholder value
    
    @staticmethod
    def rouge_score(candidate: str, reference: str) -> Dict[str, Dict[str, float]]:
        """Calculate ROUGE score for explanation quality.
        
        This is a placeholder. In a real implementation, you would use:
        from rouge import Rouge
        
        Args:
            candidate: Candidate explanation text
            reference: Reference explanation text
            
        Returns:
            Dictionary with ROUGE scores
        """
        # Placeholder implementation
        # In real implementation: 
        # rouge = Rouge()
        # return rouge.get_scores(candidate, reference)[0]
        return {
            "rouge-1": {"f": 0.7, "p": 0.68, "r": 0.72},
            "rouge-2": {"f": 0.65, "p": 0.63, "r": 0.67},
            "rouge-l": {"f": 0.68, "p": 0.66, "r": 0.70}
        }  # Placeholder values
    
    @staticmethod
    def meteor_score(candidate: str, reference: str) -> float:
        """Calculate METEOR score for explanation quality.
        
        This is a placeholder. In a real implementation, you would use:
        from nltk.translate.meteor_score import meteor_score
        
        Args:
            candidate: Candidate explanation text
            reference: Reference explanation text
            
        Returns:
            METEOR score (0.0 to 1.0)
        """
        # Placeholder implementation
        # In real implementation: return meteor_score([reference.split()], candidate.split())
        return 0.65  # Placeholder value


class ImageCaptioningMetrics:
    """Metrics for evaluating image captioning quality."""
    
    @staticmethod
    def cider_score(candidate: str, references: List[str]) -> float:
        """Calculate CIDEr score for image captioning quality.
        
        This is a placeholder. In a real implementation, you would use a proper CIDEr implementation.
        
        Args:
            candidate: Candidate caption
            references: List of reference captions
            
        Returns:
            CIDEr score
        """
        # Placeholder implementation
        return 0.72  # Placeholder value


class LatencyMetrics:
    """Metrics for measuring LLM response latency."""
    
    @staticmethod
    def measure_latency(func, *args, **kwargs) -> Tuple[Any, float]:
        """Measure the latency of a function call.
        
        Args:
            func: Function to measure
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Tuple of (function result, latency in seconds)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        return result, end_time - start_time
    
    @staticmethod
    def calculate_latency_stats(latencies: List[float]) -> Dict[str, float]:
        """Calculate statistics for a list of latency measurements.
        
        Args:
            latencies: List of latency measurements in seconds
            
        Returns:
            Dictionary with mean, median, min, max, and percentile statistics
        """
        if not latencies:
            return {
                "mean": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
            
        return {
            "mean": np.mean(latencies),
            "median": np.median(latencies),
            "min": np.min(latencies),
            "max": np.max(latencies),
            "p90": np.percentile(latencies, 90),
            "p95": np.percentile(latencies, 95),
            "p99": np.percentile(latencies, 99)
        }


class BacktestMetrics:
    """Metrics for evaluating backtest performance."""
    
    @staticmethod
    def calculate_returns(prices: List[float], positions: List[int]) -> List[float]:
        """Calculate returns for a series of positions.
        
        Args:
            prices: List of prices
            positions: List of positions (-1, 0, 1) for each price
            
        Returns:
            List of returns
        """
        if len(prices) <= 1 or len(prices) != len(positions):
            return []
            
        returns = []
        for i in range(1, len(prices)):
            price_return = (prices[i] / prices[i-1]) - 1.0
            position_return = price_return * positions[i-1]
            returns.append(position_return)
            
        return returns
    
    @staticmethod
    def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio.
        
        Args:
            returns: List of returns
            risk_free_rate: Risk-free rate (annualized)
            
        Returns:
            Sharpe ratio
        """
        if not returns:
            return 0.0
            
        # Assuming returns are daily, annualize the Sharpe ratio
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
            
        # Daily Sharpe ratio
        daily_sharpe = (mean_return - risk_free_rate / 252) / std_return
        
        # Annualized Sharpe ratio (√252 is the typical annualization factor for daily returns)
        return daily_sharpe * np.sqrt(252)
    
    @staticmethod
    def maximum_drawdown(returns: List[float]) -> float:
        """Calculate maximum drawdown.
        
        Args:
            returns: List of returns
            
        Returns:
            Maximum drawdown (as a positive percentage)
        """
        if not returns:
            return 0.0
            
        # Calculate cumulative returns
        cum_returns = np.cumprod(np.array(returns) + 1.0)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(cum_returns)
        
        # Calculate drawdown
        drawdown = (running_max - cum_returns) / running_max
        
        # Return maximum drawdown
        return np.max(drawdown)
    
    @staticmethod
    def win_rate(trades: List[float]) -> float:
        """Calculate win rate.
        
        Args:
            trades: List of trade returns (each value represents the return from a single trade)
            
        Returns:
            Win rate (percentage of winning trades)
        """
        if not trades:
            return 0.0
            
        wins = sum(1 for t in trades if t > 0)
        return wins / len(trades)
    
    @staticmethod
    def profit_factor(trades: List[float]) -> float:
        """Calculate profit factor.
        
        Args:
            trades: List of trade returns
            
        Returns:
            Profit factor (gross profit / gross loss)
        """
        if not trades:
            return 0.0
            
        gross_profit = sum(t for t in trades if t > 0)
        gross_loss = abs(sum(t for t in trades if t < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
            
        return gross_profit / gross_loss