FROM nginx:1.9.8
MAINTAINER jason.umiker@gmail.com

RUN rm -f /etc/nginx/conf.d/*.conf
ADD ./bounce.conf /etc/nginx/conf.d/

EXPOSE 80
