import { defineConfig } from 'orval';

export default defineConfig({
  api: {
    input: './openapi.yml',
    output: {
      mode: 'tags-split',          // разделить по тегам
      target: './src/api/generated',
      client: 'react-query',       // генерировать хуки для react-query
      schemas: './src/api/generated/models',
      override: {
        mutator: './src/api/axios-instance.ts',
      },
    },
    hooks: {
      afterAllFilesWrite: 'prettier --write',
    },
  },
});