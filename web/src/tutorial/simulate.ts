// Stand-ins for the outside world in the tutorial: a source's own system announcing a delivery
// over its signed inbound webhook, and a delivery registered through the API.
import { api } from "../api/client";
import type { Schemas } from "../api/client";

/** Standard Webhooks signature: "v1," + base64(HMAC-SHA256(secret, "{id}.{timestamp}.{body}")). */
export async function signWebhook(
  secretText: string,
  id: string,
  timestamp: number,
  body: string,
  subtle: SubtleCrypto | null = globalThis.crypto?.subtle ?? null,
): Promise<string> {
  const raw = Uint8Array.from(atob(secretText.replace(/^whsec_/, "")), (c) => c.charCodeAt(0));
  const message = new TextEncoder().encode(`${id}.${timestamp}.${body}`);
  let signature: Uint8Array;
  if (subtle) {
    const key = await subtle.importKey("raw", raw, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    signature = new Uint8Array(await subtle.sign("HMAC", key, message));
  } else {
    signature = hmacSha256(raw, message); // browsers only offer crypto.subtle on https or localhost
  }
  return "v1," + btoa(String.fromCharCode(...signature));
}

// --- HMAC-SHA256 for pages served over plain http (FIPS 180-4, RFC 2104) ----------------------

const K = Uint32Array.from([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01,
  0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
  0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
  0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08,
  0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
  0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]);

export function sha256(data: Uint8Array): Uint8Array {
  const length = data.length;
  const padded = new Uint8Array(Math.ceil((length + 9) / 64) * 64);
  padded.set(data);
  padded[length] = 0x80;
  const view = new DataView(padded.buffer);
  view.setUint32(padded.length - 8, Math.floor(length / 0x20000000));
  view.setUint32(padded.length - 4, (length << 3) >>> 0);
  const h = Uint32Array.from([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const w = new Uint32Array(64);
  const rotr = (x: number, n: number) => (x >>> n) | (x << (32 - n));
  for (let block = 0; block < padded.length; block += 64) {
    for (let i = 0; i < 16; i++) w[i] = view.getUint32(block + i * 4);
    for (let i = 16; i < 64; i++) {
      const s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
      const s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
      w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, hh] = h;
    for (let i = 0; i < 64; i++) {
      const t1 = (hh + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i]) >>> 0;
      const t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
      [hh, g, f, e, d, c, b, a] = [g, f, e, (d + t1) >>> 0, c, b, a, (t1 + t2) >>> 0];
    }
    [a, b, c, d, e, f, g, hh].forEach((v, i) => (h[i] = (h[i] + v) >>> 0));
  }
  const out = new Uint8Array(32);
  const outView = new DataView(out.buffer);
  h.forEach((v, i) => outView.setUint32(i * 4, v));
  return out;
}

export function hmacSha256(key: Uint8Array, message: Uint8Array): Uint8Array {
  const block = new Uint8Array(64);
  block.set(key.length > 64 ? sha256(key) : key);
  const inner = new Uint8Array(64 + message.length);
  const outer = new Uint8Array(64 + 32);
  for (let i = 0; i < 64; i++) {
    inner[i] = block[i] ^ 0x36;
    outer[i] = block[i] ^ 0x5c;
  }
  inner.set(message, 64);
  outer.set(sha256(inner), 64);
  return sha256(outer);
}

/** Delivery details priced at the allocation's quoted rate. */
async function deliveryFor(allocationId: string, delivered: number, extra: Record<string, unknown>) {
  const allocation = await api<Schemas["Allocation"]>(`/v1/allocations/${allocationId}`);
  return {
    allocation_id: allocationId,
    delivered_count: delivered,
    spend: (Number(allocation.quoted_unit_rate) * delivered).toFixed(2),
    ...extra,
  };
}

/** Posts a signed `batch.delivered` message to an inbound webhook, as the source's system would. */
export async function sendSignedDelivery(endpointId: string, allocationId: string): Promise<string> {
  const { secret } = await api<Schemas["WebhookSecret"]>(`/v1/inbound-webhooks/${endpointId}/secret`);
  const id = `msg_tutorial_${Date.now()}`;
  const timestamp = Math.floor(Date.now() / 1000);
  const data = await deliveryFor(allocationId, 1200, {
    reported_metrics: { agreement: 0.91 },
    contributor_count: 18,
    external_ref: `tutorial-${Date.now()}`,
    notes: "Sent by the tutorial, standing in for the source's own system.",
  });
  const body = JSON.stringify({ type: "batch.delivered", data });
  const response = await fetch(`/v1/inbound/${endpointId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "webhook-id": id,
      "webhook-timestamp": String(timestamp),
      "webhook-signature": await signWebhook(secret, id, timestamp, body),
    },
    body,
  });
  const out = (await response.json()) as Schemas["InboundResult"] & { detail?: string };
  if (!response.ok) throw new Error(out.detail ?? `The webhook answered ${response.status}.`);
  return out.batch_id;
}

/** Registers a delivery through the API, as a script or integration would. */
export async function registerDelivery(allocationId: string): Promise<string> {
  const body = await deliveryFor(allocationId, 600, {
    reported_metrics: { agreement: 0.74 },
    contributor_count: 9,
    notes: "Sent by the tutorial. The source reports rater agreement of 0.74; the spec asks for 0.85.",
  });
  const batch = await api<Schemas["Batch"]>("/v1/batches", { method: "POST", body });
  return batch.id;
}
