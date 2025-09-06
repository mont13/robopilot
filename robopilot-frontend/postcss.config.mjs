/** @type {import('postcss-load-config').Config} */
const config = {
  plugins: {
    "@tailwindcss/postcss": {
      cssTransforms: {
        // Use cssnano instead of lightningcss
        minify: false,
      },
    },
    cssnano: {
      preset: "default",
    },
  },
};

export default config;
