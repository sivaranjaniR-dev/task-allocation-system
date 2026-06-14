// Auto hide flash messages after 3 seconds
setTimeout(function() {
    let alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        alert.style.display = 'none';
    });
}, 3000);

// Confirm before delete
function confirmDelete() {
    return confirm('Are you sure you want to delete?');
}
