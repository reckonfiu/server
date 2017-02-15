FROM python:2.7.10
WORKDIR /reckonfiu
ADD . /reckonfiu
RUN pip install -r requirements.txt
CMD ["python", "-u" ,"app/server.py"]
