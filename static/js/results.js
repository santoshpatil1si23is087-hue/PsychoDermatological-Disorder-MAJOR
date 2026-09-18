console.log('Results.js loaded successfully');

document.addEventListener('DOMContentLoaded', function() {
    const results = JSON.parse(sessionStorage.getItem('analysisResults'));
    
    if (!results) {
        window.location.href = '/detection';
        return;
    }

    displayResults(results);
});

function displayResults(results) {
    // Display skin condition results
    document.getElementById('resultImage').src = `/static/uploads/${results.image_path}`;
    document.getElementById('skinCondition').textContent = results.skin_condition;
    
    const confidence = results.skin_confidence;
    const confidenceBar = document.getElementById('confidenceBar');
    const confidenceText = document.getElementById('confidenceText');
    
    // Animate confidence bar
    setTimeout(() => {
        confidenceBar.style.width = confidence + '%';
    }, 300);
    
    confidenceText.textContent = confidence.toFixed(2) + '%';
    
    // Set confidence bar color based on confidence level
    confidenceBar.classList.remove('from-green-400', 'to-green-600', 'from-yellow-400', 'to-yellow-600', 'from-red-400', 'to-red-600');
    
    if (confidence >= 80) {
        confidenceBar.classList.add('from-green-400', 'to-green-600');
        confidenceText.classList.add('text-green-600');
    } else if (confidence >= 60) {
        confidenceBar.classList.add('from-yellow-400', 'to-yellow-600');
        confidenceText.classList.remove('text-green-600');
        confidenceText.classList.add('text-yellow-600');
    } else {
        confidenceBar.classList.add('from-red-400', 'to-red-600');
        confidenceText.classList.remove('text-green-600');
        confidenceText.classList.add('text-red-600');
    }
    
    // Display GAD-7 results
    document.getElementById('gad7Score').textContent = results.gad7_score;
    const gad7SeverityBadge = document.getElementById('gad7Severity');
    gad7SeverityBadge.textContent = results.gad7_severity;
    gad7SeverityBadge.className = 'px-4 py-2 font-bold rounded-lg text-sm ' + getBadgeClass(results.gad7_severity);
    
    // Animate GAD-7 bar
    setTimeout(() => {
        document.getElementById('gad7Bar').style.width = (results.gad7_score / 21 * 100) + '%';
    }, 500);
    
    // Display PHQ-9 results
    document.getElementById('phq9Score').textContent = results.phq9_score;
    const phq9SeverityBadge = document.getElementById('phq9Severity');
    phq9SeverityBadge.textContent = results.phq9_severity;
    phq9SeverityBadge.className = 'px-4 py-2 font-bold rounded-lg text-sm ' + getBadgeClass(results.phq9_severity);
    
    // Animate PHQ-9 bar
    setTimeout(() => {
        document.getElementById('phq9Bar').style.width = (results.phq9_score / 27 * 100) + '%';
    }, 700);
    
    // Display recommendations with delay
    setTimeout(() => {
        displayRecommendations(results.recommendations);
    }, 2000);
}

function getBadgeClass(severity) {
    const severityLower = severity.toLowerCase();
    
    if (severityLower.includes('minimal') || severityLower.includes('none')) {
        return 'bg-green-500 text-white';
    } else if (severityLower.includes('mild')) {
        return 'bg-yellow-500 text-white';
    } else if (severityLower.includes('moderate')) {
        return 'bg-blue-500 text-white';
    } else if (severityLower.includes('severe') || severityLower.includes('moderately severe')) {
        return 'bg-red-500 text-white';
    } else {
        return 'bg-gray-500 text-white';
    }
}

function displayRecommendations(recommendations) {
    document.getElementById('loadingRecommendations').style.display = 'none';
    document.getElementById('recommendations').style.display = 'block';
    
    const formattedRecommendations = formatMarkdown(recommendations);
    document.getElementById('recommendationsContent').innerHTML = formattedRecommendations;
}

function formatMarkdown(text) {
    // Convert headers with Tailwind styling
    text = text.replace(/^### (.*$)/gim, '<h3 class="text-xl font-bold text-gray-800 mt-6 mb-3">$1</h3>');
    text = text.replace(/^## (.*$)/gim, '<h2 class="text-2xl font-bold text-gray-800 mt-6 mb-4">$1</h2>');
    text = text.replace(/^# (.*$)/gim, '<h1 class="text-3xl font-bold text-gray-800 mt-6 mb-4">$1</h1>');
    
    // Convert bold and italic
    text = text.replace(/\*\*\*(.+?)\*\*\*/g, '<strong class="font-bold text-gray-900"><em>$1</em></strong>');
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold text-gray-900">$1</strong>');
    text = text.replace(/\*(.+?)\*/g, '<em class="italic">$1</em>');
    
    // Convert lists
    text = text.replace(/^\* (.+)$/gim, '<li class="ml-6 mb-2">$1</li>');
    text = text.replace(/^- (.+)$/gim, '<li class="ml-6 mb-2">$1</li>');
    text = text.replace(/^(\d+)\. (.+)$/gim, '<li class="ml-6 mb-2">$2</li>');
    
    // Wrap lists in ul tags with styling
    text = text.replace(/(<li.*?<\/li>)/s, '<ul class="list-disc list-inside space-y-2 my-4">$1</ul>');
    
    // Convert line breaks to paragraphs with styling
    text = text.replace(/\n\n/g, '</p><p class="mb-4 text-gray-700 leading-relaxed">');
    text = '<p class="mb-4 text-gray-700 leading-relaxed">' + text + '</p>';
    
    return text;
}