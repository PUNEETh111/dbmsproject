/**
 * app.js — Client-Side JavaScript
 * Smart College Event Management System
 * Handles flash message auto-dismiss and UI interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss flash messages after 5 seconds
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-10px)';
            setTimeout(() => flash.remove(), 500);
        }, 5000);
    });

    // Confirm before delete actions
    document.querySelectorAll('.confirm-delete').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Animate stat numbers on scroll
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const final = parseInt(el.textContent);
                    if (isNaN(final)) return;
                    let current = 0;
                    const step = Math.ceil(final / 30);
                    const timer = setInterval(() => {
                        current += step;
                        if (current >= final) {
                            el.textContent = final;
                            clearInterval(timer);
                        } else {
                            el.textContent = current;
                        }
                    }, 30);
                    observer.unobserve(el);
                }
            });
        });
        statValues.forEach(el => observer.observe(el));
    }
});
