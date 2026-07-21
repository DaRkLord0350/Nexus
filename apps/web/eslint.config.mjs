import nextConfig from 'eslint-config-next';

const config = [
  ...nextConfig,
  {
    rules: {
      // Flags the standard "fetch on mount" pattern (calling an async
      // function from useEffect that sets state once data resolves) as if
      // state were being set synchronously during the effect body. That
      // pattern is used deliberately and correctly throughout this app.
      'react-hooks/set-state-in-effect': 'warn',
      // False-positives on `const Icon = iconFor(...)` — selecting between a
      // handful of existing icon components isn't defining a new component.
      'react-hooks/static-components': 'warn',
    },
  },
];

export default config;
