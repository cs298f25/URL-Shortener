const API_URL = '';

function showMessage(message, isError = false) {
    const msgDiv = document.getElementById('message');
    msgDiv.className = isError ? 'alert alert-error' : 'alert alert-success';
    msgDiv.textContent = message;
    setTimeout(() => msgDiv.innerHTML = '', 3000);
}

async function addLink() {
    const url = document.getElementById('url').value;
    const code = document.getElementById('code').value;

    if (!url) {
        showMessage('Please enter a URL', true);
        return;
    }

    try {
        const response = await fetch(`/add`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ url, code: code || undefined })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(`Link shortened! Code: ${data.short_code}`);
            document.getElementById('url').value = '';
            document.getElementById('code').value = '';
            loadLinks();
        } else {
            showMessage(data.error, true);
        }
    } catch (error) {
        showMessage('Error connecting to server', true);
    }
}

async function deleteLink(code) {
    if (!confirm(`Delete link "${code}"?`)) return;

    try {
        const response = await fetch(`/delete`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ code })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Link deleted successfully');
            loadLinks();
        } else {
            showMessage(data.error, true);
        }
    } catch (error) {
        showMessage('Error connecting to server', true);
    }
}

async function loadLinks() {
    try {
        const response = await fetch(`/links`);
        const links = await response.json();

        const container = document.getElementById('links-container');
        
        if (Object.keys(links).length === 0) {
            container.innerHTML = '<div class="empty-state">No links yet. Create your first one!</div>';
            return;
        }

        container.innerHTML = '<div class="links-list">' +
            Object.entries(links).map(([code, url]) => `
                <div class="link-item">
                    <div class="link-info">
                        <div class="short-code">${code}</div>
                        <div class="original-url">${url}</div>
                    </div>
                    <button class="btn-delete" onclick="deleteLink('${code}')">Delete</button>
                </div>
            `).join('') +
            '</div>';
    } catch (error) {
        showMessage('Error loading links', true);
    }
}

loadLinks();