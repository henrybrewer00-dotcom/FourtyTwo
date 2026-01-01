/**
 * GAME 42 - Authentication JavaScript
 * Handles logout functionality across all pages
 */

document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('logout-btn');

    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function() {
            try {
                const res = await fetch('/api/logout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (res.ok) {
                    window.location.href = '/auth';
                } else {
                    alert('Logout failed. Please try again.');
                }
            } catch (err) {
                console.error('Logout error:', err);
                alert('Connection error. Please try again.');
            }
        });
    }
});
