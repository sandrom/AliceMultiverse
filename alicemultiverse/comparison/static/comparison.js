// Comparison interface JavaScript

let currentComparison = null;
let selectedWinner = null;
let selectedStrength = 'clear';

// Load next comparison
async function loadNextComparison() {
    try {
        const response = await fetch('/comparison/next');
        if (!response.ok) {
            throw new Error('Failed to load comparison');
        }
        
        const data = await response.json();
        if (!data) {
            showMessage('No more comparisons available');
            return;
        }
        
        currentComparison = data;
        displayComparison(data);
        resetSelection();
    } catch (error) {
        console.error('Error loading comparison:', error);
        showMessage('Error loading comparison');
    }
}

// Display comparison images
function displayComparison(comparison) {
    const imageA = document.getElementById('image-a');
    const imageB = document.getElementById('image-b');
    
    // Clear previous images
    imageA.innerHTML = '<div class="loading">Loading...</div>';
    imageB.innerHTML = '<div class="loading">Loading...</div>';
    
    // Load image A
    const imgA = new Image();
    imgA.onload = () => {
        imageA.innerHTML = '';
        imageA.appendChild(imgA);
    };
    imgA.onerror = () => {
        imageA.innerHTML = '<div class="error">Failed to load image</div>';
    };
    // Use the path directly as it might be absolute
    imgA.src = `/static/images/${encodeURIComponent(comparison.asset_a.path)}`;
    
    // Load image B
    const imgB = new Image();
    imgB.onload = () => {
        imageB.innerHTML = '';
        imageB.appendChild(imgB);
    };
    imgB.onerror = () => {
        imageB.innerHTML = '<div class="error">Failed to load image</div>';
    };
    // Use the path directly as it might be absolute
    imgB.src = `/static/images/${encodeURIComponent(comparison.asset_b.path)}`;
}

// Select winner
function selectWinner(winner) {
    selectedWinner = winner;
    
    // Update button states
    document.querySelectorAll('.control-button').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    if (winner === 'a') {
        document.getElementById('btn-a').classList.add('selected');
    } else if (winner === 'b') {
        document.getElementById('btn-b').classList.add('selected');
    } else if (winner === 'tie') {
        document.getElementById('btn-tie').classList.add('selected');
    }
    
    // Show strength selector for non-tie votes
    const strengthSelector = document.getElementById('strength-selector');
    const submitBtn = document.getElementById('submit-btn');
    
    if (winner !== 'tie') {
        strengthSelector.style.display = 'flex';
        submitBtn.style.display = 'block';
    } else {
        strengthSelector.style.display = 'none';
        submitBtn.style.display = 'block';
    }
}

// Select strength
function selectStrength(strength) {
    selectedStrength = strength;
    
    // Update button states
    document.querySelectorAll('.strength-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    event.target.classList.add('active');
}

// Submit vote
async function submitVote() {
    if (!currentComparison || !selectedWinner) {
        return;
    }
    
    try {
        const response = await fetch('/comparison/vote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                comparison_id: currentComparison.id,
                winner: selectedWinner,
                strength: selectedWinner === 'tie' ? null : selectedStrength,
            }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit vote');
        }
        
        // Load next comparison
        await loadNextComparison();
    } catch (error) {
        console.error('Error submitting vote:', error);
        showMessage('Error submitting vote');
    }
}

// Reset selection
function resetSelection() {
    selectedWinner = null;
    selectedStrength = 'clear';
    
    document.querySelectorAll('.control-button').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    document.querySelectorAll('.strength-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase() === 'clear') {
            btn.classList.add('active');
        }
    });
    
    document.getElementById('strength-selector').style.display = 'none';
    document.getElementById('submit-btn').style.display = 'none';
}

// Show stats modal
async function showStats() {
    try {
        const response = await fetch('/comparison/stats');
        if (!response.ok) {
            throw new Error('Failed to load stats');
        }
        
        const stats = await response.json();
        displayStats(stats);
        
        document.getElementById('stats-modal').classList.add('active');
    } catch (error) {
        console.error('Error loading stats:', error);
        showMessage('Error loading stats');
    }
}

// Display stats in table
function displayStats(stats) {
    const tbody = document.querySelector('#stats-table tbody');
    tbody.innerHTML = '';
    
    stats.forEach((model, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${model.model}</td>
            <td class="rating">${Math.round(model.rating)}</td>
            <td>${model.comparison_count}</td>
            <td class="win-rate">${(model.win_rate * 100).toFixed(1)}%</td>
        `;
        tbody.appendChild(row);
    });
}

// Hide stats modal
function hideStats() {
    document.getElementById('stats-modal').classList.remove('active');
}

// Show message
function showMessage(message) {
    // TODO: Implement toast notification
    console.log(message);
}

// Keyboard shortcuts
document.addEventListener('keydown', (event) => {
    // Prevent shortcuts when modal is open
    if (document.getElementById('stats-modal').classList.contains('active')) {
        if (event.key === 'Escape') {
            hideStats();
        }
        return;
    }
    
    switch (event.key.toLowerCase()) {
        case 'a':
        case 'arrowleft':
            event.preventDefault();
            selectWinner('a');
            break;
        case 'b':
        case 'arrowright':
            event.preventDefault();
            selectWinner('b');
            break;
        case '=':
        case ' ':
            event.preventDefault();
            selectWinner('tie');
            break;
        case '1':
            if (selectedWinner && selectedWinner !== 'tie') {
                selectStrength('slight');
            }
            break;
        case '2':
            if (selectedWinner && selectedWinner !== 'tie') {
                selectStrength('clear');
            }
            break;
        case '3':
            if (selectedWinner && selectedWinner !== 'tie') {
                selectStrength('strong');
            }
            break;
        case '4':
            if (selectedWinner && selectedWinner !== 'tie') {
                selectStrength('decisive');
            }
            break;
        case 'enter':
            event.preventDefault();
            if (selectedWinner) {
                submitVote();
            }
            break;
        case 'escape':
            resetSelection();
            break;
    }
});

// Close modal on background click
document.getElementById('stats-modal').addEventListener('click', (event) => {
    if (event.target === event.currentTarget) {
        hideStats();
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadNextComparison();
});