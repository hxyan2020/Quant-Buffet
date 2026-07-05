module.exports = {
  apps: [
    {
      name: "quant-buffet",
      cwd: "/opt/quant-buffet/.next/standalone",
      script: "server.js",
      env: {
        NODE_ENV: "production",
        PORT: "3088",
        HOSTNAME: "0.0.0.0",
        DATABASE_URL: "file:/var/lib/quant-buffet/dev.db",
      },
    },
  ],
};
