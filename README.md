# URL-Shortener

A Flask-based URL shortener service with Redis backend, deployed on AWS EC2 with automatic SSL certificate management.

**Authors:** Jake Morro, Cole Aydelotte

Development process described in [developers.md](docs/developers.md)

## Prerequisites

- AWS EC2 instance (Amazon Linux 2 recommended)
- Security group configured with the following inbound rules:
  - Port 22 (SSH)
  - Port 80 (HTTP)
  - Port 443 (HTTPS)
- SSH access to your EC2 instance
- Your DNS registration token from the course

## Deployment Instructions

### Step 1: Connect to Your EC2 Instance

SSH into your EC2 instance:

```bash
ssh -i your-key.pem ec2-user@your-ec2-ip-address
```

### Step 2: Run the Deployment Script

Copy and paste the entire `up.sh` script into your terminal:

```bash
sudo yum -y install git
git clone https://github.com/cs298f25/URL-Shortener.git
cd URL-Shortener
echo USERNAME=yourusername
echo LABEL=web
echo TOKEN=your-bearer-token-here
nano .env
./register_ip.sh
./ec2_deploy.sh
```

### Step 3: Configure Environment Variables

When the `nano .env` command opens the editor, replace the placeholder values:

```
USERNAME=yourusername
LABEL=web
TOKEN=your-bearer-token-here
```

Replace:
- `yourusername` with your actual username
- `your-bearer-token-here` with your DNS registration token

Save and exit nano (Ctrl+X, then Y, then Enter).

### Step 4: Update Subdomain in ec2_deploy.sh

Before running `./ec2_deploy.sh`, you need to edit the SUBDOMAIN variable:

```bash
nano ec2_deploy.sh
```

Find the line:
```bash
SUBDOMAIN="aydelottecweb"
```

Change it to match your username and label (e.g., if USERNAME=jsmith and LABEL=web, use "jsmithweb").

Save and exit (Ctrl+X, then Y, then Enter).

### Step 5: Complete Deployment

The scripts will automatically:
1. Register your EC2 IP address with the DNS service
2. Install and configure Redis
3. Set up Python virtual environment and dependencies
4. Generate SSL certificates using Let's Encrypt
5. Deploy and start the Flask application

During SSL certificate generation, you'll be prompted for:
- Your email address
- Agreement to Let's Encrypt Terms of Service

## What Gets Deployed

- **Redis 6**: In-memory data store for URL mappings
- **Flask Application**: Web service running on HTTPS
- **SSL Certificate**: Automatic HTTPS via Let's Encrypt
- **Systemd Services**: Automatic startup on reboot

## Accessing Your Application

After successful deployment, your URL shortener will be available at:

```
https://[username][label].moraviancs.click
```

For example: `https://jsmithweb.moraviancs.click`

## Useful Commands

### Service Management

```bash
# View Flask application logs
sudo journalctl -u flask -f

# View Redis logs
sudo journalctl -u redis6 -f

# Restart Flask service
sudo systemctl restart flask

# Restart Redis service
sudo systemctl restart redis6

# Check service status
sudo systemctl status flask
sudo systemctl status redis6
```

### SSL Certificate Management

```bash
# Renew SSL certificate
sudo certbot renew

# Test certificate renewal
sudo certbot renew --dry-run
```

## Troubleshooting

### Port 80/443 Already in Use

If you get errors about ports being in use, check what's running:

```bash
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443
```

Stop conflicting services before running deployment.

### Service Won't Start

Check the service logs:

```bash
sudo journalctl -u flask -n 50
sudo journalctl -u redis6 -n 50
```

### DNS Not Resolving

Verify your subdomain registration:

```bash
nslookup [username][label].moraviancs.click
```

If it doesn't resolve, re-run `./register_ip.sh`

## Project Structure

```
URL-Shortener/
├── app/
│   ├── requirements.txt
│   └── [application files]
├── flask.service
├── ec2_deploy.sh
├── register_ip.sh
├── up.sh
└── .env (created during deployment)
```

## Security Notes

- Never commit `.env` files to version control
- Keep your bearer token secure
- SSL certificates are automatically renewed by certbot
- Redis runs locally and is not exposed externally

## Certificate Locations

After deployment, certificates are stored at:

```
Certificate: /etc/letsencrypt/live/[subdomain].moraviancs.click/fullchain.pem
Private Key: /etc/letsencrypt/live/[subdomain].moraviancs.click/privkey.pem
```

## Support

For issues or questions, refer to the course documentation or contact your instructor.

---

## Local Development

For local development and testing:

### Redis Setup

The application persists link data in Redis instead of JSON files.

1. Install Redis:
   - macOS: `brew install redis`
   - Other platforms: See https://redis.io/docs/getting-started/installation/

2. Start a local Redis server with default configuration:
   ```bash
   redis-server
   ```
   The app assumes `redis://localhost:6379/0` when `REDIS_URL` is not set.

3. (Optional) Point the app to a different Redis instance:
   ```bash
   export REDIS_URL=redis://<host>:<port>/<db>
   ```

### Running Locally

With Redis running:

```bash
cd app
pip install -r requirements.txt
flask run
```

All short code mappings will be stored under the `link:` namespace in Redis.