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
});
