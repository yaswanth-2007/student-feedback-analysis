/**
 * Student Feedback Form Interactive Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    const feedbackForm = document.getElementById('studentFeedbackForm');
    if (!feedbackForm) return;

    const progressBar = document.getElementById('surveyProgressBar');
    const progressText = document.getElementById('surveyProgressText');
    const requiredSections = document.querySelectorAll('.survey-question-block[data-required="true"]');
    const totalRequired = requiredSections.length;

    function updateProgress() {
        if (totalRequired === 0) return;
        
        let answeredRequired = 0;
        requiredSections.forEach(block => {
            const radioChecked = block.querySelector('input[type="radio"]:checked');
            const textarea = block.querySelector('textarea');
            if (radioChecked || (textarea && textarea.value.trim() !== '')) {
                answeredRequired++;
            }
        });

        const percentage = Math.round((answeredRequired / totalRequired) * 100);
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
        }
        if (progressText) {
            progressText.textContent = `${answeredRequired} of ${totalRequired} required questions completed (${percentage}%)`;
        }
    }

    // Attach listeners to rating radios and text inputs
    const inputs = feedbackForm.querySelectorAll('input[type="radio"], textarea');
    inputs.forEach(input => {
        input.addEventListener('change', updateProgress);
        input.addEventListener('input', updateProgress);
    });

    // Form submission validation
    feedbackForm.addEventListener('submit', (e) => {
        let firstMissingBlock = null;
        requiredSections.forEach(block => {
            const radioChecked = block.querySelector('input[type="radio"]:checked');
            const textarea = block.querySelector('textarea');
            const isValid = radioChecked || (textarea && textarea.value.trim() !== '');

            if (!isValid) {
                block.classList.add('border-danger');
                if (!firstMissingBlock) firstMissingBlock = block;
            } else {
                block.classList.remove('border-danger');
            }
        });

        if (firstMissingBlock) {
            e.preventDefault();
            firstMissingBlock.scrollIntoView({ behavior: 'smooth', block: 'center' });
            alert('Please complete all required feedback questions before submitting.');
        } else {
            // Disable submit button to prevent accidental double-submit
            const submitBtn = document.getElementById('submitFeedbackBtn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Submitting Anonymously...';
            }
        }
    });

    // Initialize initial progress
    updateProgress();
});
