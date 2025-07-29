# Use the same base image for consistency
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the frontend dependency file
COPY ./requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire frontend source code into the container
COPY . /app

# Expose the default Streamlit port
EXPOSE 8501

# The command to run the Streamlit application
# We use --server.address 0.0.0.0 to make it accessible from outside the container
CMD ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]