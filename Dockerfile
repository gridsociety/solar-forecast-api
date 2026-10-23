FROM python:3.9-slim

RUN mkdir -p /app
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY . app.py /app/
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/openapi.json', timeout=3).close()"
CMD ["app.py"]
ENTRYPOINT [ "python" ]
