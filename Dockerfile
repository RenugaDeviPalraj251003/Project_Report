# Use an official Python runtime as the base image
FROM python:3.11-slim

# Install necessary dependencies for Chrome
RUN apt-get update && apt-get install -y wget gnupg unzip

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get update && apt-get install -y google-chrome-stable

# Install Chromedriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+') && \
    CHROMEDRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION) && \
    wget https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver_linux64.zip

# Set environment variables
ENV PATH="/usr/local/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy project files to the working directory
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port Flask is running on
EXPOSE 5000

# Define the default command to run the app using Gunicorn
CMD ["gunicorn", "app:analyser", "--bind", "0.0.0.0:5000"]

