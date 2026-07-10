export type ApiHealth = {
  app: string;
  version: string;
  environment: string;
  database: string;
  ai_provider: string;
  external_ai_enabled: boolean;
};
