#!/bin/sh
if [ ! -f /etc/nginx/ssl/intellicore.amdocs.com.crt ] || [ ! -f /etc/nginx/ssl/intellicore.amdocs.com.key ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/intellicore.amdocs.com.key \
    -out /etc/nginx/ssl/intellicore.amdocs.com.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=intellicore.amdocs.com"
    echo "Self-signed SSL certificate generated."
else
    echo "SSL certificate already exists."
fi
