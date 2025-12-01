sudo yum -y install git
git clone https://github.com/cs298f25/URL-Shortener.git
cd URL-Shortener
echo USERNAME=yourusername
echo LABEL=web
echo TOKEN=your-bearer-token-here
nano .env
./register_ip.sh
./ec2_deploy.sh