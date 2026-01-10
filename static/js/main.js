document.addEventListener('DOMContentLoaded', () => {
    // Reveal Animations on Scroll
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const fadeElements = document.querySelectorAll('.fade-in, .slide-up');
    fadeElements.forEach(el => observer.observe(el));

    // Navbar Scroll Effect
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(10, 10, 10, 0.95)';
            navbar.style.padding = '0.5rem 0';
        } else {
            navbar.style.background = 'rgba(10, 10, 10, 0.8)';
            navbar.style.padding = '0';
        }
    });

    // Mobile Navigation Toggle
    const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (mobileNavToggle) {
        mobileNavToggle.addEventListener('click', () => {
            mobileNavToggle.classList.toggle('active');
            navLinks.classList.toggle('active');
            document.body.style.overflow = navLinks.classList.contains('active') ? 'hidden' : '';
        });

        // Close menu when clicking a link
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileNavToggle.classList.remove('active');
                navLinks.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
    }

    // Image Modal Functionality
    const modal = document.getElementById('imageModal');
    if (modal) {
        const modalImg = document.getElementById("modalImage");
        const captionText = document.getElementById("caption");
        const span = document.getElementsByClassName("close")[0];

        // Open Modal
        // Open Modal
        document.querySelectorAll('.enlarge-image, .enlarge-card').forEach(el => {
            el.addEventListener('click', function (e) {
                // If clicking a link or button inside the card, do not open modal
                if (e.target.closest('a') || e.target.closest('button')) {
                    return;
                }

                e.stopPropagation();
                e.stopPropagation();

                // Get data from attributes
                const title = this.getAttribute('data-title');
                const issuer = this.getAttribute('data-issuer');
                const date = this.getAttribute('data-date');
                const desc = this.getAttribute('data-description');
                const link = this.getAttribute('data-link');
                const imgSrc = this.getAttribute('data-image');

                if (imgSrc) {
                    modalImg.src = imgSrc;
                    modalImg.alt = title;

                    // Populate other fields
                    document.getElementById('modalTitle').textContent = title;
                    document.getElementById('modalIssuer').textContent = issuer;
                    document.getElementById('modalDescription').textContent = desc;
                    document.getElementById('modalDate').textContent = date;

                    const btn = document.getElementById('modalLink');
                    if (link && link !== '#') {
                        btn.href = link;
                        btn.style.display = 'inline-flex';
                    } else {
                        btn.style.display = 'none';
                    }

                    modal.style.display = "block";
                    // Force reflow
                    void modal.offsetWidth;
                    modal.classList.add('show');
                }
            });
        });

        // Close Modal Helper
        const closeModal = () => {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = "none";
            }, 300); // Match transition duration
        };

        // Close on X
        if (span) {
            span.onclick = closeModal;
        }

        // Close on click outside
        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Close on Escape
        document.addEventListener('keydown', function (event) {
            if (event.key === "Escape" && modal.style.display === "block") {
                closeModal();
            }
        });
    }
});
