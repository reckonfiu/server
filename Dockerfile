FROM python:2.7.10
WORKDIR /reconfiu
ADD . /reconfiu
RUN pip install -r requirements.txt
CMD ["python", "app/server.py"]
