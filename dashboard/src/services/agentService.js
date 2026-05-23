/**
 * agentService.js
 * Placeholder service for LangGraph AI agent integration
 * Replace AGENT_URL with your LangGraph Cloud endpoint when ready
 * UI components consume this API - swap backend without touching components
 */

const AGENT_URL = process.env.REACT_APP_AGENT_URL || null;

const agentService = {
  /**
   * Ask the AI agent a question about claims
   * Returns mock response when AGENT_URL is not configured
   */
  ask: async (question, claims = []) => {
    if (!AGENT_URL) {
      return agentService._mockResponse(question, claims);
    }
    const res = await fetch(`${AGENT_URL}/v1/runs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, context: claims.slice(0, 50) })
    });
    if (!res.ok) throw new Error(`Agent error: HTTP ${res.status}`);
    return res.json();
  },

  /** Mock AI response for demo mode when LangGraph is not connected */
  _mockResponse: (question, claims) => {
    const q = question.toLowerCase();
    let filtered = claims;
    let label = 'all claims';

    if (q.includes('paid')) { filtered = claims.filter(c => c.status === 'PAID'); label = 'paid claims'; }
    else if (q.includes('denied')) { filtered = claims.filter(c => c.status === 'DENIED'); label = 'denied claims'; }
    else if (q.includes('pending')) { filtered = claims.filter(c => c.status === 'PENDING'); label = 'pending claims'; }

    if (q.includes('high') || q.includes('large') || q.includes('value')) {
      filtered = filtered.filter(c => (c.amountBilled || 0) > 5000);
      label = `high-value ${label}`;
    }

    const total = filtered.reduce((s, c) => s + (c.amountBilled || 0), 0);

    return {
      answer: `I found ${filtered.length} ${label} with a total value of $${total.toLocaleString()}.`,
      claims: filtered.slice(0, 12),
      steps: [
        { label: 'Understand question', time: '0.8s' },
        { label: 'Fetch claims (MECP API)', time: '1.2s' },
        { label: `Filter ${label}`, time: '0.3s' },
        { label: 'Generate response', time: '0.6s' }
      ],
      sources: ['MECP Claims API /v1/resources/claims']
    };
  }
};

export default agentService;
