docker build -f Dockerfile-build -t shibbolth .
echo "docker run --name=shibboleth -d -it --rm -p 8080:8080 shibtest run-jetty.sh" > run.sh
