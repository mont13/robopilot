FROM node:22

# Install build dependencies
RUN apt-get update && apt-get install -y python3 make g++ python3-pip

# Create a non-root user to own the application code
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

WORKDIR /home/appuser/frontend

# Install dependencies based on the preferred package manager
COPY --chown=appuser:appuser package.json package-lock.json* ./
RUN npm ci

# Expose the port the app will run on
EXPOSE 3000

# Set correct permissions and switch to non-root user for better security
RUN chown -R appuser:appuser /home/appuser
USER appuser

# Start the application in development mode with hot reloading enabled
CMD ["npm", "run", "dev", "--", "--turbopack"]
