/**
 * useClaims.js
 * React hook - separates data fetching from UI rendering
 * Components consume this hook, never call claimsApi directly
 */

import { useState, useEffect, useCallback } from 'react';
import claimsApi from '../services/claimsApi';

export function useClaims() {
  const [claims, setClaims]     = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [connected, setConnected] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await claimsApi.getAll(2000);
      setClaims(data.claims || []);
      setConnected(true);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err.message);
      setConnected(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [load]);

  const stats = {
    total:   claims.length,
    paid:    claims.filter(c => c.status === 'PAID').length,
    denied:  claims.filter(c => c.status === 'DENIED').length,
    pending: claims.filter(c => c.status === 'PENDING').length,
    totalBilled:  claims.reduce((s, c) => s + (c.amountBilled  || 0), 0),
    totalPaid:    claims.filter(c => c.status === 'PAID').reduce((s, c) => s + (c.amountPaid    || 0), 0),
    totalAllowed: claims.filter(c => c.status === 'PAID').reduce((s, c) => s + (c.amountAllowed || 0), 0),
    deniedExposure:  claims.filter(c => c.status === 'DENIED').reduce((s, c)  => s + (c.amountBilled || 0), 0),
    pendingExposure: claims.filter(c => c.status === 'PENDING').reduce((s, c) => s + (c.amountBilled || 0), 0),
  };

  return { claims, loading, error, connected, lastRefresh, stats, refresh: load };
}

export function useAgentSession() {
  const [messages, setMessages] = useState([]);
  const [steps, setSteps]       = useState([]);
  const [thinking, setThinking] = useState(false);
  const [sessionId]             = useState(() => Math.random().toString(36).slice(2, 10));

  const addMessage = (role, content, resultClaims = [], resultSteps = []) => {
    setMessages(prev => [...prev, { role, content, claims: resultClaims, id: Date.now() }]);
    if (resultSteps.length) setSteps(resultSteps);
  };

  return { messages, steps, thinking, setThinking, addMessage, sessionId };
}
