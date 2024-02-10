# Use the official Python 3.12.1 image as a base image
FROM python:3.12.1

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the pyproject.toml and poetry.lock files into the container
COPY pyproject.toml poetry.lock /app/

# Configure Poetry to not create a virtual environment and install dependencies globally
RUN poetry config virtualenvs.create false

# Install the project dependencies
RUN poetry install --no-interaction --no-ansi

# Copy the rest of the application code into the container
COPY . /app

# Command to run the application using uvicorn
CMD ["uvicorn", "schema:app", "--host", "0.0.0.0", "--port", "8000"]
