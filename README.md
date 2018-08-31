# Nginx Proxy for auto-cert SSL

This was built by one of our developers @logzilla Corp. 

It works so well that I told him he should share it but he didn't have time.

So here it is.

# Support

We can't support this, but it's too awesome not to share :)

# Contributing

Please create a pull request if you like.

# Install

1. Install `docker` and `docker-compose`

2. Set the helper script and sslproxy home:

```
cp proxyedit /usr/local/bin/
adduser sslproxy
cp -rp ./sslproxy/* /home/
chown -R sslproxy:sslproxy /home/sslproxy
```

3. Run the instances (note: the nginx image **MUST** use ports 80 and 443 in order for Letsencrypt to work


```
cd /home/sslproxy/proxy
docker-compose up
```


# Usage

1. Start the Nginx docker image

1. Create a DNS entry for your redirected host, we'll use `foo.logzilla.net` as an example below.

2. Verify that DNS is working using something like https://www.whatsmydns.net **before** running `proxyedit` below.

Run `proxyedit` to create a new redirect.

Sample config:

## Basic Redirect to internal IP

The internal host can be http or https, doesn't matter.

```
'foo.logzilla.net': {
  'target': 'http://1.2.3.4',
}
```

## Host with port

```
'foo.logzilla.net': {
        'target': 'http://1.2.3.4:8080',
}
```


## Redirect With Websockets

```
'foo.logzilla.net': {
        'target': 'http://1.2.3.4',
        'extra_config': [
            'location /ws/ {',
                'proxy_pass http://1.2.3.4;',
                'proxy_http_version 1.1;',
                'proxy_connect_timeout 1;',
                'proxy_set_header Upgrade $http_upgrade;',
                'proxy_set_header Connection "Upgrade";',
            '}',
        ]
    }
```

#### That *should* be all you need. I may have forgotten something since I wrote this README from memory.




