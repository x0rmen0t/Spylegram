FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip


RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY . /app/

CMD ["python", "main.py"]
