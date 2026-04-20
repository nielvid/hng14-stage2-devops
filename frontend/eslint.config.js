module.exports = [
  {
    files: ["**/*.js"],
    ignores: ["eslint.config.js"],
    rules: {
      "no-unused-vars": ["error", { "caughtErrorsIgnorePattern": "^_" }],
      "no-undef": "error",
      "eqeqeq": "error",
      "no-console": "off"
    },
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "commonjs",
      globals: {
        require: "readonly",
        module: "readonly",
        exports: "readonly",
        process: "readonly",
        __dirname: "readonly",
        console: "readonly",
        setTimeout: "readonly"
      }
    }
  }
];
