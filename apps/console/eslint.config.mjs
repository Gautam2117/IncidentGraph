import nextVitals from "eslint-config-next/core-web-vitals";

const config = [
  ...nextVitals,
  {
    ignores: [".next/**", "playwright-report/**", "test-results/**", "next-env.d.ts"],
  },
];

export default config;
