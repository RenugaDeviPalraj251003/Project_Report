document.addEventListener("DOMContentLoaded", function () {
    const navLinks = document.querySelectorAll("nav a");

    for (let link of navLinks) {
        link.addEventListener("click", function (event) {
            event.preventDefault();
            const targetId = this.getAttribute("href").substring(1);
            const targetElement = document.getElementById(targetId);

            window.scrollTo({
                top: targetElement.offsetTop,
                behavior: "smooth"
            });
        });
    }
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

