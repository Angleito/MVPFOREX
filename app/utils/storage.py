"""
Storage system for historical model performance data.
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

class PerformanceStorage:
    """Storage system for historical model performance data."""
    
    def __init__(self, db_path: str = "results/performance/history.db"):
        """Initialize the storage system.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Create tables
            c.executescript("""
                CREATE TABLE IF NOT EXISTS evaluation_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp DATETIME,
                    metadata TEXT
                );
                
                CREATE TABLE IF NOT EXISTS pattern_recognition_metrics (
                    run_id TEXT,
                    model TEXT,
                    accuracy REAL,
                    precision REAL,
                    recall REAL,
                    f1 REAL,
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs (run_id)
                );
                
                CREATE TABLE IF NOT EXISTS explanation_quality_metrics (
                    run_id TEXT,
                    model TEXT,
                    bleu REAL,
                    rouge_1 REAL,
                    rouge_2 REAL,
                    rouge_l REAL,
                    meteor REAL,
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs (run_id)
                );
                
                CREATE TABLE IF NOT EXISTS backtest_metrics (
                    run_id TEXT,
                    model TEXT,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    win_rate REAL,
                    profit_factor REAL,
                    total_return REAL,
                    num_trades INTEGER,
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs (run_id)
                );
                
                CREATE TABLE IF NOT EXISTS latency_metrics (
                    run_id TEXT,
                    model TEXT,
                    mean REAL,
                    std REAL,
                    min REAL,
                    max REAL,
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs (run_id)
                );
                
                CREATE TABLE IF NOT EXISTS user_feedback (
                    run_id TEXT,
                    model TEXT,
                    rating INTEGER,
                    comment TEXT,
                    feedback_type TEXT,
                    timestamp DATETIME,
                    FOREIGN KEY (run_id) REFERENCES evaluation_runs (run_id)
                );
            """)
    
    def store_evaluation_results(self, results: Dict[str, Dict[str, Any]], metadata: Optional[Dict] = None) -> str:
        """Store evaluation results in the database.
        
        Args:
            results: Dictionary with evaluation results for each model
            metadata: Optional metadata about the evaluation run
            
        Returns:
            run_id for the stored results
        """
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Store evaluation run
            c.execute(
                "INSERT INTO evaluation_runs (run_id, timestamp, metadata) VALUES (?, ?, ?)",
                (run_id, datetime.now(), json.dumps(metadata or {}))
            )
            
            # Store metrics for each model
            for model, model_data in results.items():
                # Pattern recognition metrics
                pattern_data = model_data.get('pattern_recognition', {})
                c.execute(
                    """INSERT INTO pattern_recognition_metrics 
                       (run_id, model, accuracy, precision, recall, f1)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (run_id, model, 
                     pattern_data.get('accuracy', 0),
                     pattern_data.get('precision', 0),
                     pattern_data.get('recall', 0),
                     pattern_data.get('f1', 0))
                )
                
                # Explanation quality metrics
                exp_data = model_data.get('explanation_quality', {})
                rouge_data = exp_data.get('rouge', {})
                c.execute(
                    """INSERT INTO explanation_quality_metrics
                       (run_id, model, bleu, rouge_1, rouge_2, rouge_l, meteor)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (run_id, model,
                     exp_data.get('bleu', 0),
                     rouge_data.get('rouge-1', {}).get('f', 0),
                     rouge_data.get('rouge-2', {}).get('f', 0),
                     rouge_data.get('rouge-l', {}).get('f', 0),
                     exp_data.get('meteor', 0))
                )
                
                # Backtest metrics
                backtest_data = model_data.get('backtest', {})
                c.execute(
                    """INSERT INTO backtest_metrics
                       (run_id, model, sharpe_ratio, max_drawdown, win_rate,
                        profit_factor, total_return, num_trades)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (run_id, model,
                     backtest_data.get('sharpe_ratio', 0),
                     backtest_data.get('max_drawdown', 0),
                     backtest_data.get('win_rate', 0),
                     backtest_data.get('profit_factor', 0),
                     backtest_data.get('total_return', 0),
                     backtest_data.get('num_trades', 0))
                )
                
                # Latency metrics
                latency_data = model_data.get('latency', {})
                c.execute(
                    """INSERT INTO latency_metrics
                       (run_id, model, mean, std, min, max)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (run_id, model,
                     latency_data.get('mean', 0),
                     latency_data.get('std', 0),
                     latency_data.get('min', 0),
                     latency_data.get('max', 0))
                )
        
        return run_id
    
    def store_user_feedback(self, run_id: str, model: str, rating: int, 
                          comment: Optional[str] = None, 
                          feedback_type: str = "general") -> None:
        """Store user feedback for a model.
        
        Args:
            run_id: ID of the evaluation run
            model: Name of the model
            rating: Numerical rating (typically 1-5)
            comment: Optional feedback comment
            feedback_type: Type of feedback (e.g., "general", "accuracy", "usefulness")
        """
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO user_feedback 
                   (run_id, model, rating, comment, feedback_type, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (run_id, model, rating, comment, feedback_type, datetime.now())
            )
    
    def get_historical_performance(self, 
                                model: Optional[str] = None,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve historical performance data.
        
        Args:
            model: Optional model name to filter results
            start_date: Optional start date for the query
            end_date: Optional end date for the query
            
        Returns:
            Dictionary with historical performance data
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # Base query conditions
            conditions = []
            params = []
            
            if model:
                conditions.append("model = ?")
                params.append(model)
            if start_date:
                conditions.append("r.timestamp >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("r.timestamp <= ?")
                params.append(end_date)
                
            where_clause = " AND ".join(conditions)
            if where_clause:
                where_clause = "WHERE " + where_clause
            
            # Query each metric type
            metrics = {}
            
            # Pattern recognition metrics
            c.execute(f"""
                SELECT p.*, r.timestamp
                FROM pattern_recognition_metrics p
                JOIN evaluation_runs r ON p.run_id = r.run_id
                {where_clause}
                ORDER BY r.timestamp
            """, params)
            metrics['pattern_recognition'] = [dict(row) for row in c.fetchall()]
            
            # Explanation quality metrics
            c.execute(f"""
                SELECT e.*, r.timestamp
                FROM explanation_quality_metrics e
                JOIN evaluation_runs r ON e.run_id = r.run_id
                {where_clause}
                ORDER BY r.timestamp
            """, params)
            metrics['explanation_quality'] = [dict(row) for row in c.fetchall()]
            
            # Backtest metrics
            c.execute(f"""
                SELECT b.*, r.timestamp
                FROM backtest_metrics b
                JOIN evaluation_runs r ON b.run_id = r.run_id
                {where_clause}
                ORDER BY r.timestamp
            """, params)
            metrics['backtest'] = [dict(row) for row in c.fetchall()]
            
            # Latency metrics
            c.execute(f"""
                SELECT l.*, r.timestamp
                FROM latency_metrics l
                JOIN evaluation_runs r ON l.run_id = r.run_id
                {where_clause}
                ORDER BY r.timestamp
            """, params)
            metrics['latency'] = [dict(row) for row in c.fetchall()]
            
            return metrics
    
    def get_user_feedback(self,
                       model: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       feedback_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve user feedback data.
        
        Args:
            model: Optional model name to filter results
            start_date: Optional start date for the query
            end_date: Optional end date for the query
            feedback_type: Optional feedback type to filter
            
        Returns:
            List of feedback entries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            conditions = []
            params = []
            
            if model:
                conditions.append("model = ?")
                params.append(model)
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date)
            if feedback_type:
                conditions.append("feedback_type = ?")
                params.append(feedback_type)
                
            where_clause = " AND ".join(conditions)
            if where_clause:
                where_clause = "WHERE " + where_clause
                
            c.execute(f"""
                SELECT *
                FROM user_feedback
                {where_clause}
                ORDER BY timestamp DESC
            """, params)
            
            return [dict(row) for row in c.fetchall()]