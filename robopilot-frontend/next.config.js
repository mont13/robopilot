/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // This will be replaced with the value from docker-compose environment variable
    NEXT_PUBLIC_API_URL:
      process.env.REACT_APP_API_URL || "http://localhost:8009",
  },
};

module.exports = nextConfig;
