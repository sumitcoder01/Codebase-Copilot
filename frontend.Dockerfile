# Step 1: Use the same base image for consistency and size.
FROM python:3.11-slim

# Step 2: Set the working directory inside the container.
WORKDIR /app

# Step 3: Copy the frontend requirements file to leverage layer caching.
COPY ./frontend/requirements.txt /app/requirements.txt

# Step 4: Install the Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the entire frontend source code into the container.
COPY ./frontend /app

# Step 6: Expose the default Streamlit port.
EXPOSE 8501

# Step 7: The command to run the Streamlit application.
# --server.address 0.0.0.0 is necessary to make it accessible outside the container.
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]