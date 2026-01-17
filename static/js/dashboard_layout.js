document.addEventListener('DOMContentLoaded', () => {
    // --- Tab Switching Logic ---
    const navItems = document.querySelectorAll('.sidebar-nav-item');
    const contentSections = document.querySelectorAll('.dashboard-content-section');

    function setActiveTab(tabId) {
        // Update Nav State
        navItems.forEach(item => {
            if (item.getAttribute('data-tab') === tabId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Update Content State
        contentSections.forEach(section => {
            if (section.id === tabId) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });

        // Update Mobile Title
        const activeLink = document.querySelector(`.sidebar-nav-item[data-tab="${tabId}"]`);
        if (activeLink) {
            const titleText = activeLink.innerText.trim();
            // Remove icon if present in text (simple split or replace)
            // The icon is in a span, innerText usually captures it. Let's just use the text node or clean it.
            // Actually innerText of the link is "👤 Profile Settings" which is fine to show in header or just "Profile Settings"
            // Let's strip the first character (emoji/icon) if it exists and a space

            const cleanTitle = titleText.replace(/^.\s/, '');
            const mobileTitle = document.querySelector('.mobile-title');
            if (mobileTitle) mobileTitle.textContent = cleanTitle;
        }

        // Persist selection (optional, for refresh)
        localStorage.setItem('adminActiveTab', tabId);
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            setActiveTab(tabId);

            // On mobile, close sidebar after selection
            if (window.innerWidth <= 768) {
                document.querySelector('.admin-container').classList.remove('sidebar-open');
            }
        });
    });

    // Restore last active tab or default to 'profile'
    const savedTab = localStorage.getItem('adminActiveTab');
    if (savedTab && document.getElementById(savedTab)) {
        setActiveTab(savedTab);
    } else {
        setActiveTab('section-profile');
    }


    // --- Mobile Sidebar Toggle ---
    const toggleBtn = document.getElementById('sidebar-toggle');
    const closeBtn = document.getElementById('sidebar-close');
    const container = document.querySelector('.admin-container');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            container.classList.toggle('sidebar-open');
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            container.classList.remove('sidebar-open');
        });
    }

    // --- Delete Confirmation (Existing Logic) ---
    const deleteLinks = document.querySelectorAll('.btn-delete');
    deleteLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const href = link.getAttribute('data-href');

            Swal.fire({
                title: 'Are you sure?',
                text: "You won't be able to revert this!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#ff6b6b',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Yes, delete it!',
                background: '#1a1a1a',
                color: '#fff'
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = href;
                }
            });
        });
    });


    // --- Edit Testimonial Logic ---
    const editBtns = document.querySelectorAll('.btn-edit');
    const editModal = document.getElementById('edit-testimonial-modal');
    const closeEditModalBtn = document.getElementById('close-edit-modal');
    const cancelEditBtn = document.getElementById('cancel-edit-testimonial');

    if (editModal) {
        // Open Modal & Populate
        editBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const id = btn.getAttribute('data-id');
                const name = btn.getAttribute('data-name');
                const message = btn.getAttribute('data-message');

                document.getElementById('edit-id').value = id;
                document.getElementById('edit-name').value = name;
                document.getElementById('edit-message').value = message;

                editModal.classList.add('active');
            });
        });

        // Close Modal Handlers
        function closeEditModal(e) {
            if (e) e.preventDefault();
            editModal.classList.remove('active');
        }

        if (closeEditModalBtn) closeEditModalBtn.addEventListener('click', closeEditModal);
        if (cancelEditBtn) cancelEditBtn.addEventListener('click', closeEditModal);
    }
});
