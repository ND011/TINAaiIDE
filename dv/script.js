document.addEventListener('DOMContentLoaded', function() {
    const greetBtn = document.getElementById('greetBtn');
    const messageDiv = document.getElementById('message');

    greetBtn.addEventListener('click', function() {
        messageDiv.textContent = 'Hello, welcome to DV!';
    });
});