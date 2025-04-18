"""
Metrics module for evaluating LLM performance.
Includes implementations for:
- Chart pattern recognition accuracy (F1 score)
- NLP metrics (BLEU, ROUGE, METEOR)
- Image captioning metrics (CIDEr)
- Latency measurement
- Backtest metrics (Sharpe ratio, drawdown)
"""

import time
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.meteor_score import meteor_score
import re

# Ensure NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')


def measure_latency(func):
    """
    Decorator to measure the execution time of a function.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    return wrapper


def calculate_bleu_score(reference_texts: List[str], candidate_text: str) -> float:
    """
    Calculate BLEU score for text quality evaluation.
    
    Args:
        reference_texts: List of reference texts
        candidate_text: Generated text to evaluate
        
    Returns:
        BLEU score (0-1 where higher is better)
    """
    # Tokenize texts
    reference_tokens = [nltk.word_tokenize(ref.lower()) for ref in reference_texts]
    candidate_tokens = nltk.word_tokenize(candidate_text.lower())
    
    # Calculate BLEU score
    weights = (0.25, 0.25, 0.25, 0.25)  # Default weights for BLEU-4
    return sentence_bleu(reference_tokens, candidate_tokens, weights=weights)


def calculate_rouge_score(reference_text: str, candidate_text: str) -> Dict[str, float]:
    """
    Calculate ROUGE score for text similarity.
    A simple implementation of ROUGE-L.
    
    Args:
        reference_text: Reference text
        candidate_text: Generated text to evaluate
        
    Returns:
        Dictionary with ROUGE precision, recall, and F1 score
    """
    # Tokenize texts
    reference_tokens = nltk.word_tokenize(reference_text.lower())
    candidate_tokens = nltk.word_tokenize(candidate_text.lower())
    
    # Find longest common subsequence
    lcs_length = _longest_common_subsequence(reference_tokens, candidate_tokens)
    
    # Calculate precision, recall, and F1
    if len(candidate_tokens) == 0:
        precision = 0
    else:
        precision = lcs_length / len(candidate_tokens)
    
    if len(reference_tokens) == 0:
        recall = 0
    else:
        recall = lcs_length / len(reference_tokens)
    
    if precision + recall == 0:
        f1 = 0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def _longest_common_subsequence(sequence1: List[str], sequence2: List[str]) -> int:
    """
    Calculate the length of the longest common subsequence between two sequences.
    Used for ROUGE-L calculation.
    """
    m, n = len(sequence1), len(sequence2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if sequence1[i - 1] == sequence2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]


def calculate_meteor_score(reference_texts: List[str], candidate_text: str) -> float:
    """
    Calculate METEOR score for semantic similarity.
    
    Args:
        reference_texts: List of reference texts
        candidate_text: Generated text to evaluate
        
    Returns:
        METEOR score (0-1 where higher is better)
    """
    # Tokenize texts
    reference_tokens = [nltk.word_tokenize(ref.lower()) for ref in reference_texts]
    candidate_tokens = nltk.word_tokenize(candidate_text.lower())
    
    # Calculate METEOR score
    scores = [meteor_score([ref], candidate_tokens) for ref in reference_tokens]
    return np.mean(scores)


def calculate_pattern_recognition_accuracy(predictions: List[str], ground_truth: List[str]) -> Dict[str, float]:
    """
    Calculate accuracy metrics for chart pattern recognition.
    
    Args:
        predictions: List of predicted patterns
        ground_truth: List of actual patterns
        
    Returns:
        Dictionary with precision, recall, F1 score, and accuracy
    """
    # Count true positives, false positives, false negatives
    tp, fp, fn = 0, 0, 0
    for pred, truth in zip(predictions, ground_truth):
        if pred == truth and pred != "none":
            tp += 1
        elif pred != truth and pred != "none":
            fp += 1
        elif pred != truth and truth != "none":
            fn += 1
    
    # Calculate precision, recall, F1 score
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # Calculate accuracy
    correct = sum(1 for p, t in zip(predictions, ground_truth) if p == t)
    accuracy = correct / len(predictions) if len(predictions) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'accuracy': accuracy
    }


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio for backtest evaluation.
    
    Args:
        returns: List of percentage returns (e.g., [0.01, -0.005, 0.02])
        risk_free_rate: Annual risk-free rate (default: 2%)
        
    Returns:
        Sharpe ratio
    """
    returns_array = np.array(returns)
    excess_returns = returns_array - (risk_free_rate / 252)  # Daily risk-free rate
    
    if np.std(excess_returns) == 0:
        return 0.0
    
    sharpe = np.mean(excess_returns) / np.std(excess_returns)
    annualized_sharpe = sharpe * np.sqrt(252)  # Annualize (assuming daily returns)
    
    return annualized_sharpe


def calculate_max_drawdown(cumulative_returns: List[float]) -> float:
    """
    Calculate maximum drawdown for backtest evaluation.
    
    Args:
        cumulative_returns: List of cumulative returns
        
    Returns:
        Maximum drawdown as a positive percentage
    """
    if not cumulative_returns:
        return 0.0
        
    cumulative_returns = np.array(cumulative_returns)
    peak = np.maximum.accumulate(cumulative_returns)
    drawdown = (peak - cumulative_returns) / peak
    max_drawdown = np.max(drawdown)
    
    return max_drawdown


def extract_trading_signals(text: str) -> Dict[str, Any]:
    """
    Extract trading signals from LLM text output.
    
    Args:
        text: LLM output text to parse
        
    Returns:
        Dictionary with extracted trading signals
    """
    signals = {
        'buy': False,
        'sell': False,
        'entry_price': None,
        'stop_loss': None,
        'take_profit': None,
        'confidence': None,
        'pattern': None
    }
    
    # Extract recommendation (buy/sell)
    buy_pattern = re.compile(r'(buy|long|bullish)', re.IGNORECASE)
    sell_pattern = re.compile(r'(sell|short|bearish)', re.IGNORECASE)
    
    if buy_pattern.search(text):
        signals['buy'] = True
    if sell_pattern.search(text):
        signals['sell'] = True
    
    # Extract price levels
    entry_pattern = re.compile(r'entry\s*(?:price|level|point)?(?:\s*:|at)?\s*\$?(\d+\.?\d*)', re.IGNORECASE)
    sl_pattern = re.compile(r'stop\s*(?:loss|out)?(?:\s*:|at)?\s*\$?(\d+\.?\d*)', re.IGNORECASE)
    tp_pattern = re.compile(r'(?:take\s*profit|target)(?:\s*:|at)?\s*\$?(\d+\.?\d*)', re.IGNORECASE)
    
    entry_match = entry_pattern.search(text)
    sl_match = sl_pattern.search(text)
    tp_match = tp_pattern.search(text)
    
    if entry_match:
        signals['entry_price'] = float(entry_match.group(1))
    if sl_match:
        signals['stop_loss'] = float(sl_match.group(1))
    if tp_match:
        signals['take_profit'] = float(tp_match.group(1))
    
    # Extract pattern
    pattern_list = [
        'fibonacci retracement', 'fib retracement',
        'head and shoulders', 'inverse head and shoulders',
        'double top', 'double bottom',
        'triangle', 'wedge', 'flag', 'pennant',
        'channel', 'support', 'resistance',
        'golden cross', 'death cross',
        'engulfing', 'doji', 'hammer', 'shooting star'
    ]
    
    for pattern in pattern_list:
        if re.search(r'\b' + re.escape(pattern) + r'\b', text, re.IGNORECASE):
            signals['pattern'] = pattern
            break
    
    # Extract confidence level
    confidence_pattern = re.compile(r'confidence(?:[: ])+(\d+)%', re.IGNORECASE)
    confidence_match = confidence_pattern.search(text)
    if confidence_match:
        signals['confidence'] = int(confidence_match.group(1)) / 100
    
    return signals