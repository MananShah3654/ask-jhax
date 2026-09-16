import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const researchRestaurant = async (payload) => {
  const { data } = await axios.post(`${API}/restaurants/research`, payload);
  return data;
};

export const getRestaurant = async (rid) => {
  const { data } = await axios.get(`${API}/restaurants/${rid}`);
  return data;
};

export const deleteRestaurant = async (rid) => {
  await axios.delete(`${API}/restaurants/${rid}`);
};

// Streams SSE from an endpoint, calling onDelta(text) per chunk, onDone() at end.
export const streamEndpoint = async (path, body, onDelta, onDone, onError, onTool, onSources) => {
  try {
    const resp = await fetch(`${API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : JSON.stringify({}),
    });
    if (!resp.ok || !resp.body) throw new Error(`HTTP ${resp.status}`);
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop();
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const json = line.slice(5).trim();
        if (!json) continue;
        try {
          const evt = JSON.parse(json);
          if (evt.type === "delta") onDelta(evt.content);
          else if (evt.type === "tool") onTool && onTool(evt);
          else if (evt.type === "sources") onSources && onSources(evt.items || []);
          else if (evt.type === "error") onError && onError(evt.content);
          else if (evt.type === "done") onDone && onDone();
        } catch (_) { /* ignore partial */ }
      }
    }
    onDone && onDone();
  } catch (e) {
    onError && onError(e.message || "stream failed");
  }
};
