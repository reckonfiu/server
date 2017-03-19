FROM python:3.5.0
WORKDIR /reconfiu
ADD . /reconfiu
RUN pip install -r requirements.txt
CMD ["python3", "-u" ,"app/server.py"]
