/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly PACKAGE_VERSION: string;
  readonly VITE_CHAT_SERVICE_URL: string;
  readonly VITE_USER_SERVICE_URL: string;
  readonly VITE_FILE_SERVICE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
