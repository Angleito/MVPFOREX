import React, { useState } from 'react';
import { getStorageItem, setStorageItem } from '../utils/storage';

export default function FeedbackPanel({ analysisId, onFeedbackSubmit }) {
  const [feedback, setFeedback] = useState('');
  const [rating, setRating] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!rating) {
      alert('Please select a rating');
      return;
    }

    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysisId,
          rating,
          feedback,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      // Store feedback in local storage to prevent duplicate submissions
      const feedbackHistory = getStorageItem('feedbackHistory', []);
      feedbackHistory.push(analysisId);
      setStorageItem('feedbackHistory', feedbackHistory);

      setSubmitted(true);
      if (onFeedbackSubmit) {
        onFeedbackSubmit({ rating, feedback });
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    }
  };

  if (submitted) {
    return (
      <div style={{
        padding: '16px',
        background: '#f0fdf4',
        border: '1px solid #bbf7d0',
        borderRadius: '8px',
        textAlign: 'center',
        color: '#166534'
      }}>
        Thank you for your feedback!
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} style={{
      padding: '20px',
      background: '#fff',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      maxWidth: '600px',
      margin: '0 auto'
    }}>
      <h3 style={{
        margin: '0 0 16px 0',
        fontSize: '18px',
        color: '#333'
      }}>
        How helpful was this analysis?
      </h3>

      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '20px',
        justifyContent: 'center'
      }}>
        {[1, 2, 3, 4, 5].map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => setRating(value)}
            style={{
              width: '40px',
              height: '40px',
              border: rating === value ? '2px solid #3b82f6' : '1px solid #e5e7eb',
              borderRadius: '50%',
              background: rating === value ? '#eff6ff' : '#fff',
              color: rating === value ? '#3b82f6' : '#6b7280',
              cursor: 'pointer',
              fontSize: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s'
            }}
          >
            {value}
          </button>
        ))}
      </div>

      <textarea
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="Additional comments (optional)"
        style={{
          width: '100%',
          padding: '12px',
          border: '1px solid #e5e7eb',
          borderRadius: '6px',
          minHeight: '100px',
          marginBottom: '16px',
          fontSize: '14px',
          resize: 'vertical'
        }}
      />

      <button
        type="submit"
        style={{
          width: '100%',
          padding: '12px',
          background: '#3b82f6',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          fontSize: '16px',
          cursor: 'pointer',
          transition: 'background-color 0.2s'
        }}
        onMouseOver={(e) => e.target.style.background = '#2563eb'}
        onMouseOut={(e) => e.target.style.background = '#3b82f6'}
      >
        Submit Feedback
      </button>
    </form>
  );
}