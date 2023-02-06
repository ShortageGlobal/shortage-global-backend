FROM python:3.10.7
ENV PYTHONDONTWRITEBYTECODE 1
WORKDIR /project
COPY requirements.txt /project/
RUN pip install -r requirements.txt
COPY . /project/
RUN apt-get update && apt-get install -y wkhtmltopdf
ENV XDG_RUNTIME_DIR /tmp
