function showMessage(message, isError = false) {
    const msgDiv = document.getElementById('message');
    msgDiv.className = isError ? 'alert alert-error' : 'alert alert-success';
    msgDiv.textContent = message;
    setTimeout(() => msgDiv.innerHTML = '', 5000);
}

async function signup() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
        showMessage('Please enter both email and password', true);
        return;
    }

    if (password.length < 6) {
        showMessage('Password must be at least 6 characters', true);
        return;
    }

    try {
        const response = await fetch('/api/signup', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Account created successfully! Redirecting...');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            showMessage(data.error || 'Failed to create account', true);
        }
    } catch (error) {
        showMessage('Error connecting to server', true);
    }
}

async function login() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
        showMessage('Please enter both email and password', true);
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Logged in successfully! Redirecting...');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            showMessage(data.error || 'Invalid email or password', true);
        }
    } catch (error) {
        showMessage('Error connecting to server', true);
    }
}

// Allow Enter key to submit forms
document.addEventListener('DOMContentLoaded', () => {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    
    if (emailInput && passwordInput) {
        [emailInput, passwordInput].forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    if (window.location.pathname === '/signup') {
                        signup();
                    } else if (window.location.pathname === '/login') {
                        login();
                    }
                }
            });
        });
    }
});

