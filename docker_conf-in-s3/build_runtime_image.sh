docker build -f Dockerfile-build -t shibboleth .
echo "docker run --name=shibboleth -d -it --rm -p 8080:8080 shibboleth run-jetty.sh" > run.sh
echo "docker run -d --name=nginx_redirect --rm -p 8888:80 nginx_redirect" >> run.sh
chmod +x run.sh
