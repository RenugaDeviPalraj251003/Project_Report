document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for navigation links
    document.querySelectorAll('header nav a').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
     // Dark mode toggle
    const themeSwitch = document.getElementById('theme-switch');

    // Check localStorage for theme preference
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        themeSwitch.checked = true;
    }

    themeSwitch.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'enabled');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'disabled');
        }
    });
});

    // Example: Simple form validation
      // Form validation and loading animation
      const form = document.querySelector('form');
      const loadingSpinner = document.getElementById('loading');
  
      form.addEventListener('submit', function(event) {
          const urlInput = document.getElementById('url');
          if (!urlInput.value) {
              alert('Please enter a URL.');
              event.preventDefault();
          } else {
              loadingSpinner.style.display = 'flex'; // Show the loading animation
          }
      });
