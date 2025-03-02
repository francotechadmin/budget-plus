FROM node:18-alpine

WORKDIR /app

# Copy only the package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy the rest of the application code
COPY . .

# Expose the port the app will run on
EXPOSE 3000

# Start the Next.js app in development mode
CMD ["npm", "run", "dev", "--host"]
