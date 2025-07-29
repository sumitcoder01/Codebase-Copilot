# Step 1: Use an official, lightweight Python image
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
# All subsequent commands will run from here.
WORKDIR /app

# Step 3: Copy only the requirements file first to leverage Docker's layer caching.
# If requirements.txt doesn't change, Docker won't reinstall dependencies on every build.
COPY ./backend/requirements.txt /app/requirements.txt

# Step 4: Install the Python dependencies
# --no-cache-dir reduces the final image size.
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the entire backend source code into the container's working directory.
COPY ./backend /app

# Step 6: Expose the port the app will run on.
# This informs Docker which port the container will listen on.
EXPOSE 8000

# Step 7: The command to run the application when the container starts.
# We use --host 0.0.0.0 to make the server accessible from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]