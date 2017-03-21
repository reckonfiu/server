FROM python:3.4
WORKDIR /reconfiu
ADD . /reconfiu
RUN pip install -r requirements.txt
CMD ["python3", "-u" ,"app/server.py"]
