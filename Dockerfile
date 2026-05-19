# Use the official lightweight Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and keep stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /code

# Install system dependencies required for OpenCV, PyTorch, and Git
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker's build cache
COPY CODE/Acne_Type_Classification/requirements.txt /code/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

# Copy the entire workspace into the container
COPY . /code/

# Set up database migrations and static files
# We use SQLite here, but you can configure MySQL environment variables as needed
RUN python CODE/Acne_Type_Classification/manage.py migrate

# Hugging Face Spaces run with a non-root user (UID 1000)
# Create a user and grant appropriate permissions for runtime database writes and media uploads
RUN useradd -m -u 1000 user && \
    chown -R user:user /code
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose Hugging Face's default port 7860
EXPOSE 7860

# Start the Django development server bound to port 7860
CMD ["python", "CODE/Acne_Type_Classification/manage.py", "runserver", "0.0.0.0:7860"]
