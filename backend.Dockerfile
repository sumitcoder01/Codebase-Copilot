# Step 1: Use an official, lightweight Python image
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git

# Step 4: Copy only the requirements file first for layer caching
COPY ./backend/requirements.txt /app/requirements.txt

# Step 5: Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Copy the entire backend source code (respecting .dockerignore)
COPY ./backend /app

# Step 7: Expose the port the app will run on
EXPOSE 8000

# Step 8: The command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]