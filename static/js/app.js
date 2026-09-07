
// Client-side interactions
document.addEventListener('DOMContentLoaded', () => {
    // Timeout for alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    });
});
