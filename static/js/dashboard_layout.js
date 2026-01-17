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
});
