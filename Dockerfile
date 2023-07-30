FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y postgresql gcc python3-dev musl-dev vim tzdata

# Copy .env_prod into the docker container
COPY .env_prod .env

# Use python-dotenv to export the .env file variables
RUN pip install python-dotenv
RUN python -c "from dotenv import dotenv_values; print(dotenv_values('.env')['TIME_ZONE'])" > /.env_tz

# Set environment variables
ENV PYTHONDONTWRITEBITECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=`cat /.env_tz`

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
