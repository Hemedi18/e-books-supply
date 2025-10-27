document.addEventListener('DOMContentLoaded', function() {
    
    // 1. MENU TOGGLE (Hamburger)
    const toggleButton = document.getElementById('mobile-nav-toggle');
    const mainNav = document.querySelector('.main-nav');
    
    if (toggleButton && mainNav) {
        
        toggleButton.addEventListener('click', function() {
            mainNav.classList.toggle('is-open');
            
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !isExpanded);
        });

        // Funga menyu baada ya kubofya linki yoyote
        mainNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                if (mainNav.classList.contains('is-open')) {
                    mainNav.classList.remove('is-open');
                    toggleButton.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }

    // 2. THEME TOGGLE (Dark/Light Mode)
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');

    // Angalia Theme kutoka Local Storage au tumia default Light
    const savedTheme = localStorage.getItem('theme') || 'light';
    body.setAttribute('data-theme', savedTheme);
    
    const updateIcons = (theme) => {
        if (theme === 'dark') {
            sunIcon.style.display = 'none';
            moonIcon.style.display = 'inline';
        } else {
            sunIcon.style.display = 'inline';
            moonIcon.style.display = 'none';
        }
    };
    
    updateIcons(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            let currentTheme = body.getAttribute('data-theme');
            let newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            updateIcons(newTheme);
        });
    }
});