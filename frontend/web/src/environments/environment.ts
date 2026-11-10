// Detecta automáticamente la URL del backend según el dominio
function getApiUrl(): string {
  // En navegador
  if (typeof window !== 'undefined') {
    const host = window.location.host;
    // Si es Preview de Revision (contiene "git-revision")
    if (host.includes('git-revision')) {
      return 'https://fashionstore-api-git-revision-iscrisis-projects.vercel.app/api/v1';
    }
    // Si es Production
    if (host.includes('fashionstore-web.vercel.app')) {
      return 'https://fashionstore-api.vercel.app/api/v1';
    }
    // Si es localhost (desarrollo)
    if (host.includes('localhost')) {
      return 'http://localhost:8000/api/v1';
    }
  }
  // Fallback a Production
  return 'https://fashionstore-api.vercel.app/api/v1';
}

export const environment = {
  production: true,
  apiUrl: getApiUrl(),
};
