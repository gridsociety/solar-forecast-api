FROM python:3.9-slim

RUN mkdir -p /app
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY . app.py /app/
EXPOSE 8080
CMD ["app.py"]
ENTRYPOINT [ "python" ]