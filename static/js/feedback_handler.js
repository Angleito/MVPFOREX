class FeedbackHandler {
    constructor() {
        this.feedbackStore = new Map();
    }

    initializeFeedbackPanel(containerId, modelType, analysisText) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="feedback-panel">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="rating-stars" data-model="${modelType}">
                        <i class="bi bi-star" data-rating="1"></i>
                        <i class="bi bi-star" data-rating="2"></i>
                        <i class="bi bi-star" data-rating="3"></i>
                        <i class="bi bi-star" data-rating="4"></i>
                        <i class="bi bi-star" data-rating="5"></i>
                    </div>
                    <button class="btn btn-sm btn-outline-primary feedback-btn" data-model="${modelType}">
                        <i class="bi bi-chat-dots"></i> Add Feedback
                    </button>
                </div>
                <div class="feedback-form d-none">
                    <textarea class="form-control mb-2" placeholder="Your feedback about this analysis..." rows="3"></textarea>
                    <div class="d-flex justify-content-end gap-2">
                        <button class="btn btn-sm btn-secondary cancel-feedback">Cancel</button>
                        <button class="btn btn-sm btn-primary submit-feedback">Submit</button>
                    </div>
                </div>
            </div>
        `;

        this.setupFeedbackListeners(container, modelType, analysisText);
    }

    setupFeedbackListeners(container, modelType, analysisText) {
        // Star rating functionality
        const ratingStars = container.querySelector('.rating-stars');
        const stars = ratingStars.querySelectorAll('i');

        stars.forEach(star => {
            star.addEventListener('mouseover', () => {
                const rating = parseInt(star.dataset.rating);
                this.updateStars(stars, rating, true);
            });

            star.addEventListener('mouseout', () => {
                const currentRating = this.feedbackStore.get(modelType)?.rating || 0;
                this.updateStars(stars, currentRating, false);
            });

            star.addEventListener('click', () => {
                const rating = parseInt(star.dataset.rating);
                this.saveFeedback(modelType, { rating, analysisText });
                this.updateStars(stars, rating, false);
            });
        });

        // Feedback form functionality
        const feedbackBtn = container.querySelector('.feedback-btn');
        const feedbackForm = container.querySelector('.feedback-form');
        const cancelBtn = container.querySelector('.cancel-feedback');
        const submitBtn = container.querySelector('.submit-feedback');
        const textarea = container.querySelector('textarea');

        feedbackBtn.addEventListener('click', () => {
            feedbackForm.classList.remove('d-none');
            feedbackBtn.classList.add('d-none');
        });

        cancelBtn.addEventListener('click', () => {
            feedbackForm.classList.add('d-none');
            feedbackBtn.classList.remove('d-none');
            textarea.value = this.feedbackStore.get(modelType)?.comment || '';
        });

        submitBtn.addEventListener('click', () => {
            const comment = textarea.value.trim();
            if (comment) {
                const currentFeedback = this.feedbackStore.get(modelType) || {};
                this.saveFeedback(modelType, {
                    ...currentFeedback,
                    comment,
                    analysisText
                });
                
                // Show success message
                const successAlert = document.createElement('div');
                successAlert.className = 'alert alert-success py-2 mt-2 mb-0';
                successAlert.innerHTML = '<i class="bi bi-check-circle-fill"></i> Feedback submitted successfully';
                feedbackForm.appendChild(successAlert);
                
                // Hide the alert after 3 seconds
                setTimeout(() => {
                    successAlert.remove();
                    feedbackForm.classList.add('d-none');
                    feedbackBtn.classList.remove('d-none');
                }, 3000);
            }
        });

        // Load existing feedback if any
        const existingFeedback = this.feedbackStore.get(modelType);
        if (existingFeedback) {
            this.updateStars(stars, existingFeedback.rating, false);
            textarea.value = existingFeedback.comment || '';
        }
    }

    updateStars(stars, rating, isHover) {
        stars.forEach(star => {
            const starRating = parseInt(star.dataset.rating);
            if (starRating <= rating) {
                star.classList.remove('bi-star');
                star.classList.add('bi-star-fill');
                if (isHover) {
                    star.classList.add('text-warning');
                }
            } else {
                star.classList.add('bi-star');
                star.classList.remove('bi-star-fill');
                star.classList.remove('text-warning');
            }
        });
    }

    saveFeedback(modelType, feedbackData) {
        this.feedbackStore.set(modelType, {
            ...feedbackData,
            timestamp: new Date().toISOString()
        });

        // Send feedback to server
        fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                modelType,
                ...feedbackData,
                timestamp: new Date().toISOString()
            })
        }).catch(error => {
            console.error('Error saving feedback:', error);
        });
    }

    getFeedback(modelType) {
        return this.feedbackStore.get(modelType);
    }

    getAllFeedback() {
        return Array.from(this.feedbackStore.entries()).map(([modelType, feedback]) => ({
            modelType,
            ...feedback
        }));
    }
}

// Initialize feedback handler when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.feedbackHandler = new FeedbackHandler();
});