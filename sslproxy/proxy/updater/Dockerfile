FROM certbot/certbot

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY updater.py ./
COPY nginx.conf.tpl ./

COPY etc/nginx /etc/nginx

VOLUME /etc/nginx /etc/letsencrypt /data/wellknown 

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["./updater.py"]
