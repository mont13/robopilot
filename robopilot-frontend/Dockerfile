FROM node:22-alpine AS builder

# Install build dependencies
RUN apk add --no-cache python3 make g++ build-base

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy all project files
COPY . .

# Build the application
RUN yarn run build

# Production image
FROM node:22-alpine AS production

# Install Python for node-gyp
RUN apk add --no-cache python3 make g++ build-base

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install only production dependencies
RUN yarn install --frozen-lockfile

# Copy built application from builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.js ./

EXPOSE 3000

CMD ["npm", "run", "start"]