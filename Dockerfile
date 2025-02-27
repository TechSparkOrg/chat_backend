# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose port (ensure it matches your Django settings)
EXPOSE 8000

# Collect static files (if needed)
RUN python manage.py collectstatic --noinput

# Run database migrations
RUN python manage.py migrate

# Start the Django ASGI server with Daphne for WebSockets
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "chat_backend.asgi:application"]
