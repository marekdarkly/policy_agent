# Build stage
FROM node:16-alpine as build

WORKDIR /app

# Copy frontend files
COPY frontend/ ./

# Install dependencies
RUN npm install

# Build the application
RUN npm run build

# Runtime stage
FROM node:16-alpine

WORKDIR /app

# Install serve
RUN npm install -g serve

# Copy built app from build stage
COPY --from=build /app/build ./build

# Copy env script
RUN echo '#!/bin/sh\n\
# Generate runtime env script\n\
echo "window.REACT_APP_API_URL = \"http://$REACT_APP_API_URL\";" > /app/build/env-config.js\n\
echo "window.REACT_APP_WS_URL = \"ws://$REACT_APP_WS_URL\";" >> /app/build/env-config.js\n\
# Start serve\n\
exec serve -s build -l $PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 3000

# Run the start script to inject env vars at runtime
CMD ["/app/start.sh"] 