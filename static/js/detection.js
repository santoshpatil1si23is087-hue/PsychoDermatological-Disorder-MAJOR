console.log('Detection.js loaded successfully');
let uploadedImage = null;

document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const previewImg = document.getElementById('previewImg');
    const imagePreview = document.getElementById('imagePreview');
    const uploadPrompt = document.getElementById('uploadPrompt');
    const removeImageBtn = document.getElementById('removeImage');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    uploadArea.addEventListener('click', function() {
        imageInput.click();
    });

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('border-blue-500', 'bg-blue-100');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('border-blue-500', 'bg-blue-100');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('border-blue-500', 'bg-blue-100');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleImageSelect(files[0]);
        }
    });

    imageInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleImageSelect(e.target.files[0]);
        }
    });

    removeImageBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        resetImageUpload();
    });

    uploadBtn.addEventListener('click', function() {
        if (uploadedImage) {
            uploadImage();
        }
    });

    const mentalHealthForm = document.getElementById('mentalHealthForm');
    mentalHealthForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitMentalHealthAssessment();
    });

    function handleImageSelect(file) {
        if (!file.type.match('image.*')) {
            alert('Please select a valid image file');
            return;
        }

        if (file.size > 16 * 1024 * 1024) {
            alert('File size must be less than 16MB');
            return;
        }

        uploadedImage = file;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            uploadPrompt.style.display = 'none';
            imagePreview.style.display = 'block';
            uploadBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    function resetImageUpload() {
        uploadedImage = null;
        imageInput.value = '';
        uploadPrompt.style.display = 'block';
        imagePreview.style.display = 'none';
        uploadBtn.disabled = true;
    }

    function uploadImage() {
        const formData = new FormData();
        formData.append('image', uploadedImage);

        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<span class="inline-block animate-spin mr-2">⏳</span>Uploading...';

        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                progressBar.style.width = '50%';
                progressText.textContent = 'Step 2: Mental Health Assessment';
                
                document.getElementById('step1').style.display = 'none';
                document.getElementById('step2').style.display = 'block';
                
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                alert('Error: ' + data.error);
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = 'Continue to Questionnaire <i class="bi bi-arrow-right ml-2"></i>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while uploading the image');
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = 'Continue to Questionnaire <i class="bi bi-arrow-right ml-2"></i>';
        });
    }

    function submitMentalHealthAssessment() {
        const formData = new FormData(mentalHealthForm);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="inline-block animate-spin mr-2">⏳</span>Analyzing...';

        progressBar.style.width = '100%';
        progressText.textContent = 'Analyzing Results...';

        fetch('/analyze_mental_health', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            sessionStorage.setItem('analysisResults', JSON.stringify(result));
            window.location.href = '/results';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during analysis');
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="bi bi-bar-chart-fill mr-2"></i>Analyze Results';
        });
    }
});