# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the backend dependency file
COPY ./requirements.txt /app/requirements.txt

# Install dependencies
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend source code into the container
COPY . /app

# Expose the port the app runs on
EXPOSE 8000

# The command to run the application using Uvicorn
# We use --host 0.0.0.0 to make it accessible from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]