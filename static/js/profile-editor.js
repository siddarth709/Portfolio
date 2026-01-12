document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const modal = document.getElementById('editor-modal');
    const closeBtn = document.getElementById('close-modal');
    const cancelBtn = document.getElementById('cancel-edit');
    const saveBtn = document.getElementById('save-edit');
    const cropContainer = document.getElementById('crop-container');
    const cropImage = document.getElementById('crop-image');
    const zoomSlider = document.getElementById('zoom-slider');

    // State
    let currentInput = null; // The file input currently being worked on
    let state = {
        scale: 1,
        panning: false,
        pointX: 0,
        pointY: 0,
        startX: 0,
        startY: 0,
        imgWidth: 0,
        imgHeight: 0
    };

    // Generic function to attach cropper logic to a pair of elements
    function initCropper(triggerBtnId, inputId) {
        const triggerBtn = document.getElementById(triggerBtnId);
        const fileInput = document.getElementById(inputId);

        if (!triggerBtn || !fileInput) return;

        triggerBtn.addEventListener('click', (e) => {
            e.preventDefault();
            currentInput = fileInput; // Track active input
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    cropImage.src = event.target.result;
                    currentInput = fileInput; // Ensure correct input is tracked
                    openModal();
                }
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }

    // Initialize for known inputs
    // Initialize for known inputs
    initCropper('edit-profile-btn', 'hidden-profile-input');
    initCropper('skills-img-btn', 'skills-img-input');
    initCropper('edu-img-btn', 'edu-img-input');
    initCropper('exp-img-btn', 'exp-img-input');
    // Logo inputs removed


    // --- Modal Logic ---
    cropImage.onload = () => {
        // Reset state
        state.scale = 1;
        state.pointX = 0;
        state.pointY = 0;
        zoomSlider.value = 1;

        // Center image
        state.imgWidth = cropImage.naturalWidth;
        state.imgHeight = cropImage.naturalHeight;

        // Initial fit
        const containerSize = 300;
        const scaleFit = Math.max(containerSize / state.imgWidth, containerSize / state.imgHeight);
        state.scale = scaleFit;
        zoomSlider.min = scaleFit * 0.5;
        zoomSlider.max = scaleFit * 3;
        zoomSlider.value = scaleFit;

        updateTransform();
    };

    zoomSlider.addEventListener('input', (e) => {
        state.scale = parseFloat(e.target.value);
        updateTransform();
    });

    // Pan Logic
    cropContainer.addEventListener('mousedown', (e) => {
        e.preventDefault();
        state.panning = true;
        state.startX = e.clientX - state.pointX;
        state.startY = e.clientY - state.pointY;
        cropContainer.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', (e) => {
        if (!state.panning) return;
        e.preventDefault();
        state.pointX = e.clientX - state.startX;
        state.pointY = e.clientY - state.startY;
        updateTransform();
    });

    window.addEventListener('mouseup', () => {
        state.panning = false;
        cropContainer.style.cursor = 'grab';
    });

    function updateTransform() {
        cropImage.style.transform = `translate(-50%, -50%) translate(${state.pointX}px, ${state.pointY}px) scale(${state.scale})`;
    }

    function openModal() {
        modal.classList.add('active');
    }

    function closeModal() {
        modal.classList.remove('active');
        // Do NOT clear input here; allow cancelling to keep the selection? 
        // Usually better to clear if user cancels crop?
        // But if they just wanted to inspect it? Let's leave it.
        // If they want to remove, they can't right now, but they can select another.
    }

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // Save Logic
    saveBtn.addEventListener('click', () => {
        if (!currentInput) return;

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const size = 300;
        canvas.width = size;
        canvas.height = size;

        ctx.fillStyle = '#0a0a0a'; // Background matching dark theme if image has transparency
        ctx.fillRect(0, 0, size, size);

        ctx.translate(size / 2, size / 2);
        ctx.translate(state.pointX, state.pointY);
        ctx.scale(state.scale, state.scale);
        ctx.drawImage(cropImage, -state.imgWidth / 2, -state.imgHeight / 2);

        canvas.toBlob((blob) => {
            const file = new File([blob], "cropped_image.png", { type: "image/png" });
            const container = new DataTransfer();
            container.items.add(file);
            currentInput.files = container.files;

            // Visual feedback (optional) - e.g. change button text?
            // Let's just close for now.
            modal.classList.remove('active');
        }, 'image/png');
    });

});
