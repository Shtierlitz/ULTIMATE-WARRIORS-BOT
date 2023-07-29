FROM python:3.10

# Set environment variables
ENV PYTHONDONTWRITEBITECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Europe/Moscow

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y postgresql gcc python3-dev musl-dev vim tzdata

# Set system timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install Python dependencies
RUN pip install --upgrade pip setuptools

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy project
COPY . /app

# Set permissions
RUN chmod 755 .
