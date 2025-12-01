const API_URL = '';

let currentUser = null;

/**
 * Display a message to the user.
 * @param {string} message - The message to display.
 * @param {boolean} [isError=false] - Whether the message is an error.
 */
function showMessage(message, isError = false) {
    const msgDiv = document.getElementById('message');
    msgDiv.className = isError ? 'alert alert-error' : 'alert alert-success';
    msgDiv.textContent = message;
    setTimeout(() => msgDiv.innerHTML = '', 3000);
}

/**
 * Format a Unix timestamp to a readable date string.
 * @param {string|number} timestamp - Unix timestamp in seconds.
 * @returns {string} Formatted date string or 'Never' if timestamp is invalid.
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    const date = new Date(parseInt(timestamp) * 1000);
    return date.toLocaleString();
}

/**
 * Format the time remaining until expiration.
 * @param {string|number} expiresAt - Unix timestamp when link expires.
 * @returns {string} Human-readable time remaining or 'Never expires' if no expiration.
 */
function formatTimeRemaining(expiresAt) {
    if (!expiresAt) return 'Never expires';
    
    const now = Math.floor(Date.now() / 1000);
    const expires = parseInt(expiresAt);
    const secondsRemaining = expires - now;
    
    if (secondsRemaining <= 0) return 'Expired';
    
    const days = Math.floor(secondsRemaining / (24 * 60 * 60));
    const hours = Math.floor((secondsRemaining % (24 * 60 * 60)) / (60 * 60));
    const minutes = Math.floor((secondsRemaining % (60 * 60)) / 60);
    
    if (days > 0) {
        return `Expires in ${days} day${days > 1 ? 's' : ''}`;
    } else if (hours > 0) {
        return `Expires in ${hours} hour${hours > 1 ? 's' : ''}`;
    } else if (minutes > 0) {
        return `Expires in ${minutes} minute${minutes > 1 ? 's' : ''}`;
    } else {
        return 'Expires soon';
    }
}

/**
 * Check if a link is expiring within 24 hours.
 * @param {string|number} expiresAt - Unix timestamp when link expires.
 * @returns {boolean} True if expiring within 24 hours, false otherwise.
 */
function isExpiringSoon(expiresAt) {
    if (!expiresAt) return false;
    const now = Math.floor(Date.now() / 1000);
    const expires = parseInt(expiresAt);
    const hoursRemaining = (expires - now) / (60 * 60);
    return hoursRemaining > 0 && hoursRemaining < 24;
}

/**
 * Check if the user is authenticated and update the UI.
 * @returns {Promise<boolean>} True if authenticated, false otherwise.
 */
async function checkAuth() {
    try {
        const response = await fetch('/user', {
            credentials: 'include'
        });
        
        if (response.ok) {
            currentUser = await response.json();
            updateUserDisplay();
            return true;
        } else if (response.status === 401) {
            window.location.href = '/login';
            return false;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login';
        return false;
    }
}

/**
 * Update the user display with current user information.
 */
function updateUserDisplay() {
    const userInfo = document.getElementById('user-info');
    if (userInfo && currentUser) {
        userInfo.innerHTML = `
            <span>Logged in as: <strong>${currentUser.email}</strong></span>
            <button class="btn btn-secondary" onclick="logout()">Logout</button>
        `;
    }
}

/**
 * Log out the current user.
 */
async function logout() {
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        } else {
            showMessage('Failed to logout', true);
        }
    } catch (error) {
        showMessage('Error logging out', true);
    }
}

/**
 * Add a new shortened link.
 */
async function addLink() {
    const url = document.getElementById('url').value;
    const code = document.getElementById('code').value;
    const expiresIn = document.getElementById('expires_in').value;

    if (!url) {
        showMessage('Please enter a URL', true);
        return;
    }

    try {
        const response = await fetch('/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ 
                url, 
                code: code || undefined,
                expires_in: expiresIn
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(`Link shortened! Code: ${data.short_code}`);
            document.getElementById('url').value = '';
            document.getElementById('code').value = '';
            document.getElementById('expires_in').value = 'never';
            loadLinks();
        } else {
            if (response.status === 401) {
                window.location.href = '/login';
            } else {
                showMessage(data.error, true);
            }
        }
    } catch (error) {
        showMessage('Error connecting to server', true);
    }
}

/**
 * Delete a shortened link.
 * @param {string} code - The short code of the link to delete.
 */
async function deleteLink(code) {
    if (!confirm(`Delete link "${code}"?`)) return;

    try {
        const response = await fetch('/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ code })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Link deleted successfully');
            loadLinks();
        } else {
            if (response.status === 401) {
                window.location.href = '/login';
            } else {
                showMessage(data.error, true);
            }
        }
    } catch (error) {
        showMessage('Error connecting to server', true);
    }
}

/**
 * Load and display all links for the current user.
 */
async function loadLinks() {
    try {
        const response = await fetch('/links', {
            credentials: 'include'
        });
        
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        const links = await response.json();

        const container = document.getElementById('links-container');
        
        if (links.length === 0) {
            container.innerHTML = '<div class="empty-state">No links yet. Create your first one!</div>';
            return;
        }

        container.innerHTML = '<div class="links-list">' +
            links.map(link => {
                const isExpired = link.is_expired;
                const expiresSoon = isExpiringSoon(link.expires_at);
                const expiredClass = isExpired ? 'expired' : '';
                const soonClass = expiresSoon ? 'expiring-soon' : '';
                
                return `
                <div class="link-item ${expiredClass} ${soonClass}">
                    <div class="link-info">
                        <div class="link-header">
                            <div class="short-code">${link.short_code}</div>
                            ${isExpired ? '<span class="expired-badge">Expired</span>' : ''}
                            ${expiresSoon && !isExpired ? '<span class="soon-badge">Expires Soon</span>' : ''}
                        </div>
                        <div class="original-url">${link.url}</div>
                        <div class="link-meta">
                            <div class="meta-item">
                                <strong>Created:</strong> ${formatTimestamp(link.created_at)}
                            </div>
                            <div class="meta-item">
                                <strong>Expires:</strong> ${link.expires_at ? formatTimestamp(link.expires_at) : 'Never'}
                            </div>
                            <div class="meta-item time-remaining">
                                ${formatTimeRemaining(link.expires_at)}
                            </div>
                        </div>
                    </div>
                    <button class="btn-delete" onclick="deleteLink('${link.short_code}')">Delete</button>
                </div>
            `;
            }).join('') +
            '</div>';
    } catch (error) {
        showMessage('Error loading links', true);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const authenticated = await checkAuth();
    if (authenticated) {
        loadLinks();
    }
});
