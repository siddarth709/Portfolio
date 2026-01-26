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
    // --- Advanced Animations ---

    // 1. Typing Layout
    const typingElement = document.querySelector('.typing-text');
    const roles = window.typingRoles || [
        { prefix: "an ", core: "AI/ML Enthusiast" },
        { prefix: "a ", core: "Problem Solver" },
        { prefix: "a ", core: "Creative Builder" }
    ];
    let roleIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typeDelay = 100;
    let eraseDelay = 50;
    let newTextDelay = 2000;

    function type() {
        if (!typingElement) return;

        const currentRole = roles[roleIndex];
        const fullText = currentRole.prefix + currentRole.core;

        if (isDeleting) {
            // Remove the span wrapper by resetting to plain text before deleting
            if (typingElement.innerHTML.includes('<span')) {
                typingElement.textContent = fullText;
            }
            typingElement.textContent = fullText.substring(0, charIndex - 1);
            charIndex--;
            typeDelay = eraseDelay;
        } else {
            typingElement.textContent = fullText.substring(0, charIndex + 1);
            charIndex++;
            typeDelay = 150;
        }

        if (!isDeleting && charIndex === fullText.length) {
            isDeleting = true;
            // Apply highlight only to the core part
            typingElement.innerHTML = currentRole.prefix + '<span class="cyan-highlight">' + currentRole.core + '</span>';
            typeDelay = newTextDelay;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            roleIndex++;
            if (roleIndex >= roles.length) roleIndex = 0;
        }

        setTimeout(type, typeDelay);
    }
    document.addEventListener("DOMContentLoaded", type); // Start typing loop
    if (typingElement) type();


    // 2. 3D Tilt Effect for Glass Panels
    const tiltElements = document.querySelectorAll('.glass-panel, .tile-card, .coming-soon-card');

    tiltElements.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -5; // Max tilt deg
            const rotateY = ((x - centerX) / centerX) * 5;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
            card.style.transition = 'transform 0.1s ease';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
            card.style.transition = 'transform 0.5s ease';
        });
    });

    // 3. Staggered Scroll Entrances
    // Existing observer is good, but let's add delay indices to children if they are in a grid
    const grids = document.querySelectorAll('.grid-layout, .edu-exp-grid, .skills-list-big');

    grids.forEach(grid => {
        const children = grid.children;
        Array.from(children).forEach((child, index) => {
            child.style.transitionDelay = `${index * 100}ms`; // Stagger effect
            observer.observe(child); // Ensure they are observed
            child.classList.add('fade-in'); // Ensure base class
        });
    });
    // End of previous section, continuing to Preview Modal


    // 4. Project Preview Modal
    const previewModal = document.getElementById('previewModal');
    if (previewModal) {
        const previewFrame = document.getElementById('previewFrame');
        const previewTitle = document.getElementById('previewTitle');
        const openExternallyBtn = document.getElementById('openExternallyBtn');
        const closePreview = document.querySelector('.preview-close');

        // Open Modal
        document.querySelectorAll('.preview-link').forEach(link => {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                const url = this.getAttribute('href');
                const title = this.getAttribute('data-title');

                previewTitle.textContent = title;
                previewFrame.src = url;
                openExternallyBtn.href = url;

                previewModal.style.display = "block";
                setTimeout(() => {
                    previewModal.classList.add('show');
                }, 10);
            });
        });

        // Close Modal
        const closePreviewModal = () => {
            previewModal.classList.remove('show');
            setTimeout(() => {
                previewModal.style.display = "none";
                previewFrame.src = ""; // Stop execution/playback
            }, 300);
        };

        if (closePreview) {
            closePreview.onclick = closePreviewModal;
        }

        previewModal.addEventListener('click', function (e) {
            if (e.target === previewModal) {
                closePreviewModal();
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === "Escape" && previewModal.style.display === "block") {
                closePreviewModal();
            }
        });
    }
});
