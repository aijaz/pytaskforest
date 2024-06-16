FROM python:3.10

WORKDIR /
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir pytf_flask
COPY . pytf_flask
CMD ["gunicorn", "-w 4", "-b 0.0.0.0:8001", "pytf_flask.flask_app:flask_app"]
EXPOSE 8001
