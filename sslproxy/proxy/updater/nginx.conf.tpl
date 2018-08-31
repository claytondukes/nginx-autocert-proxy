worker_processes 5;

user nobody nogroup;
pid /tmp/nginx.pid;
error_log stderr info;

events {
    worker_connections 1024;
    accept_mutex on;
}

http {
    include mime.types;
    default_type application/octet-stream;
    access_log /dev/stdout combined;
    sendfile on;
    client_max_body_size 0;

    server {
        listen 80 default_server;
        location ^~ /.well-known/ {
            allow all;
            root /data/wellknown/$host;
        }
        location / {
            rewrite ^ https://$host$request_uri? permanent;
        }
    }

    {% for host, config in local_hosts.iteritems() %}
    server {
        listen 80;
        server_name {{host}};
        location / {
            {% for line in config.extra_location_root %}
            {{line}}
            {% endfor %}
            proxy_pass {{config.target}};
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Server $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Real-IP $remote_addr;
        }
        {% for line in config.extra_config %}
        {{line}}
        {% endfor %}
    }
    {% endfor %}
    
    {% for host, config in hosts.iteritems() %}
    {% if config.cert_ready %}
    server {
        listen 443;
        server_name {{host}};
        ssl on;
        ssl_certificate /etc/letsencrypt/live/{{host}}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/{{host}}/privkey.pem;
        location / {
            {% for line in config.extra_location_root %}
            {{line}}
            {% endfor %}
            proxy_pass {{config.target}};
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Server $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Real-IP $remote_addr;
        }
        {% for line in config.extra_config %}
        {{line}}
        {% endfor %}
    }
    {% endif %}
    {% endfor %}
    
}
