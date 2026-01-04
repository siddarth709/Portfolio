document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const fileInput = document.getElementById('hidden-profile-input');
    const editBtn = document.getElementById('edit-profile-btn');
    const modal = document.getElementById('editor-modal');
    const closeBtn = document.getElementById('close-modal');
    const cancelBtn = document.getElementById('cancel-edit');
    const saveBtn = document.getElementById('save-edit');
    const cropContainer = document.getElementById('crop-container');
    const cropImage = document.getElementById('crop-image');
    const zoomSlider = document.getElementById('zoom-slider');
    const form = document.getElementById('profile-form');
    // We need a way to inject the blob into the form. 
    // Since we can't set file input value programmatically for security,
    // we will use a hidden input or append to FormData if we were using AJAX.
    // BUT, standard form submit relies on the file input.
    // TRICK: We will keep the original file input for the initial selection.
    // If the user crops, we need to swap that file content or use a DataTransfer.
    // Easier approach: Use AJAX to submit the form, or simpler:
    // Update a hidden text input with base64 data? No, valid file upload is better.
    // Let's use DataTransfer to update the file input files.

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

    // 1. Trigger File Input
    editBtn.addEventListener('click', (e) => {
        e.preventDefault();
        fileInput.click();
    });

    // 2. Handle File Selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            const reader = new FileReader();
            reader.onload = (event) => {
                cropImage.src = event.target.result;
                openModal();
            }
            reader.readAsDataURL(e.target.files[0]);
        }
    });

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

    // 3. Zoom Logic
    zoomSlider.addEventListener('input', (e) => {
        state.scale = parseFloat(e.target.value);
        updateTransform();
    });

    // 4. Pan Logic
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

    // 5. Open/Close Modal
    function openModal() {
        modal.classList.add('active');
    }

    function closeModal() {
        modal.classList.remove('active');
        fileInput.value = ''; // Reset if cancelled
    }

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // 6. Save (Crop) Logic
    saveBtn.addEventListener('click', () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const size = 300; // Output size
        canvas.width = size;
        canvas.height = size;

        // Calculate source rectangle
        // The display is 300x300. The image is at (pointX, pointY) from center, scaled by 'scale'.
        // We want to map the 300x300 visible area to the canvas.

        // Image center in container text: 150 + pointX, 150 + pointY

        // Easier: draw image transformed.

        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, size, size);

        // Move to center of canvas
        ctx.translate(size / 2, size / 2);
        // Apply same transforms
        ctx.translate(state.pointX, state.pointY);
        ctx.scale(state.scale, state.scale);
        // Draw image centered at 0,0
        ctx.drawImage(cropImage, -state.imgWidth / 2, -state.imgHeight / 2);

        canvas.toBlob((blob) => {
            // Create a new File from blob
            const file = new File([blob], "profile_pic.png", { type: "image/png" });
            const container = new DataTransfer();
            container.items.add(file);

            // Assign to input
            fileInput.files = container.files;

            // Close modal
            modal.classList.remove('active');

            // Optional: Submit immediately or show preview
            // For now, allow user to click "Update Profile" on the main form? 
            // The prompt implied "Apply" -> triggers cropping. User still needs to submit form.
            // Let's update the preview on the page if any.
            // But wait, the admin page input was inside the main form.
            // If we updated fileInput.files, normal form submit will work!

        }, 'image/png');
    });

});
