/**
 * claimsApi.js
 * Service layer for MECP MarkLogic REST API
 * Base URL proxied through serve_dashboard.py on port 8888
 * All business logic lives here - UI components never call fetch directly
 */

const BASE = '/api/v1/resources/claims';

async function get(params = '') {
  const url = params ? `${BASE}?${params}` : BASE;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: HTTP ${res.status}`);
  return res.json();
}

const claimsApi = {
  /** Fetch all claims up to limit */
  getAll: (limit = 2000) => get(`limit=${limit}`),

  /** Fetch claims filtered by status: PAID | DENIED | PENDING */
  getByStatus: (status, limit = 2000) => get(`status=${status}&limit=${limit}`),

  /** Fetch a single claim by ID e.g. CLM-0001 */
  getById: (id) => get(`id=${id}`),

  /** Health check - returns true if API responds */
  ping: async () => {
    try {
      await fetch('/api/v1/resources/claims?limit=1');
      return true;
    } catch {
      return false;
    }
  }
};

export default claimsApi;
