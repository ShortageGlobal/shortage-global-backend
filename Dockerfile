FROM python:3.9.10-slim as base
ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV prod
ENV AWS_DEFAULT_REGION=us-east-1
RUN apt-get update && apt-get install -y \
    gcc \
    libmagic-dev \
    libssl-dev \
    libpq-dev \
    swig \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /shortage_global/
COPY requirements.txt /shortage_global/
RUN pip install -r requirements.txt

FROM base as application
COPY . /shortage_global/

FROM application as collectstatic
RUN python manage.py collectstatic --noinput

# NGINX
FROM nginx:1.14 as static
# Configure NGINX
RUN mkdir -p /data/nginx/cache
RUN chown nginx:nginx /data/nginx/cache
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
# Copy static files
COPY --from=collectstatic /shortage_global/static /var/www/html/static
RUN touch /var/www/html/static/index.html