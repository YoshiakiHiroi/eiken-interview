interface AppConfig {
  apiBaseUrl: string;
  firebase: {
    apiKey: string;
    authDomain: string;
    projectId: string;
    appId: string;
  };
}

function requireEnv(name: string): string {
  const value: unknown = import.meta.env[name];
  if (typeof value !== "string" || value === "") {
    throw new Error(`Missing required environment variable ${name} (see web/.env.example)`);
  }
  return value;
}

export function loadConfig(): AppConfig {
  return {
    apiBaseUrl: requireEnv("VITE_API_BASE_URL"),
    firebase: {
      apiKey: requireEnv("VITE_FIREBASE_API_KEY"),
      authDomain: requireEnv("VITE_FIREBASE_AUTH_DOMAIN"),
      projectId: requireEnv("VITE_FIREBASE_PROJECT_ID"),
      appId: requireEnv("VITE_FIREBASE_APP_ID"),
    },
  };
}

export const CONFIG = loadConfig();
