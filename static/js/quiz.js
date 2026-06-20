/* ==========================================================================
   Learnix Practice Quiz Controller
   ========================================================================== */

let currentQuestion = 0;
let questions = [];
let answers = {}; // Maps questionId -> option chosen
let timerInterval = null;
let timeRemaining = 0;

document.addEventListener('DOMContentLoaded', () => {
    initQuiz();
});

function initQuiz() {
    questions = document.querySelectorAll('.quiz-question-card');
    if (questions.length === 0) return;
    
    // 1. Initialize indicators
    updateIndicators();
    
    // 2. Start Countdown Timer
    const container = document.querySelector('.quiz-container');
    if (container) {
        timeRemaining = parseInt(container.getAttribute('data-time-limit')) || 180;
        startTimer();
    }
}

/* 1. Timer Logic */
function startTimer() {
    const timerDisplay = document.getElementById('quizTimeRemaining');
    if (!timerDisplay) return;
    
    const updateDisplay = () => {
        const mins = Math.floor(timeRemaining / 60);
        const secs = timeRemaining % 60;
        timerDisplay.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };
    
    updateDisplay();
    
    timerInterval = setInterval(() => {
        timeRemaining--;
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            timeRemaining = 0;
            updateDisplay();
            showGlobalToast('warning', 'Time is up! Auto-submitting your quiz.');
            triggerSubmitQuiz();
        } else {
            updateDisplay();
            // Pulse orange/red on low time
            if (timeRemaining < 30) {
                timerDisplay.parentElement.style.color = '#EF4444';
                timerDisplay.parentElement.style.borderColor = 'rgba(239,68,68,0.4)';
            }
        }
    }, 1000);
}

/* 2. Pagination Navigation */
function showQuestion(index) {
    if (index < 0 || index >= questions.length) return;
    
    // Hide all
    questions.forEach(q => q.style.display = 'none');
    
    // Show target
    questions[index].style.display = 'block';
    currentQuestion = index;
    
    // Toggle controls
    const prevBtn = document.getElementById('quizPrevBtn');
    const nextBtn = document.getElementById('quizNextBtn');
    const submitBtn = document.getElementById('quizSubmitBtn');
    
    prevBtn.disabled = (index === 0);
    
    if (index === questions.length - 1) {
        nextBtn.style.display = 'none';
        submitBtn.style.display = 'inline-flex';
    } else {
        nextBtn.style.display = 'inline-flex';
        submitBtn.style.display = 'none';
    }
    
    updateIndicators();
}

function nextQuestion() {
    showQuestion(currentQuestion + 1);
}

function prevQuestion() {
    showQuestion(currentQuestion - 1);
}

function updateIndicators() {
    const dots = document.querySelectorAll('.page-indicator-dot');
    dots.forEach((dot, idx) => {
        dot.className = 'page-indicator-dot';
        if (idx === currentQuestion) {
            dot.style.background = '#4F46E5';
            dot.style.transform = 'scale(1.25)';
        } else {
            dot.style.transform = 'scale(1)';
            // If answered, make it green
            const qCard = questions[idx];
            const qId = qCard.querySelector('[name^="q-"]') ? qCard.querySelector('[name^="q-"]').name.split('-')[1] : null;
            
            // Check if answers has key
            if (qId && answers[qId]) {
                dot.style.background = '#10B981';
            } else if (!qId && qCard.querySelector('.fill-in-box') && qCard.querySelector('.fill-in-box').value.trim() !== '') {
                // Special check for fill-in blank cards
                dot.style.background = '#10B981';
            } else {
                dot.style.background = 'rgba(255, 255, 255, 0.1)';
            }
        }
    });
}

/* 3. Option selection hooks */
function selectOption(questionId, value, cardElement) {
    // Check radio inside card
    const input = cardElement.querySelector('input');
    if (input) input.checked = true;
    
    // Visual toggling
    const sibs = cardElement.parentElement.querySelectorAll('.option-card');
    sibs.forEach(s => s.classList.remove('selected'));
    cardElement.classList.add('selected');
    
    // Save to answers state
    answers[questionId] = value;
    
    // Update indicator dot
    updateIndicators();
}

function saveFillAnswer(questionId, value) {
    answers[questionId] = value;
    updateIndicators();
}

/* 4. Submission calls */
function triggerSubmitQuiz() {
    clearInterval(timerInterval);
    
    const container = document.querySelector('.quiz-container');
    const quizId = parseInt(container.getAttribute('data-quiz-id'));
    
    // Hide active play view, show submits loader
    const playPanel = document.getElementById('activeQuizPlayPanel');
    const loader = document.getElementById('quizSubmittingLoader');
    
    if (playPanel) playPanel.style.display = 'none';
    if (loader) loader.style.display = 'block';
    
    // API Request
    const payload = {
        quiz_id: quizId,
        answers: answers
    };
    
    fetch('/api/quiz/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Reload page to let server render graded layout
            window.location.reload();
        } else {
            showGlobalToast('danger', data.message || 'Failed to submit quiz.');
            if (playPanel) playPanel.style.display = 'block';
            if (loader) loader.style.display = 'none';
        }
    })
    .catch(err => {
        console.error('Quiz submit failed:', err);
        showGlobalToast('danger', 'Error connecting to Quiz submissions endpoint.');
        if (playPanel) playPanel.style.display = 'block';
        if (loader) loader.style.display = 'none';
    });
}
