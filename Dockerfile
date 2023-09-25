FROM python:3.9-slim
WORKDIR /app

COPY requirements.txt /app/

RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY . /app/

COPY snooper.session /app/snooper.session

CMD ["python", "main.py"]
