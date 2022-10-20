FROM python:3.8-slim

RUN apt-get update
RUN apt-get install gcc -y
RUN apt update
RUN apt upgrade
RUN apt install python3-dev -y
RUN apt install libxml2-dev -y
RUN apt install libxslt1-dev -y
RUN apt install zlib1g-dev -y
RUN apt install g++ -y

RUN pip install python-telegram-bot==13.14
RUN pip install opencv-python==4.5.5.64
RUN pip install faiss-cpu==1.7.2
RUN pip install cython==0.29.14
RUN pip install onnxruntime==1.12.1
RUN pip install insightface==0.6.2
RUN pip install sqlitedict==2.0.0
WORKDIR /usr/src/app
COPY . .

RUN chmod +x /usr/src/app
ENTRYPOINT ["python","./telebot.py"]