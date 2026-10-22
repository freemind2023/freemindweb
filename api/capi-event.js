// Forwards a browser-side Meta Pixel event to the Conversions API server-side,
// so the event survives ad blockers / Safari ITP / browser tracking restrictions.
// Requires META_CAPI_ACCESS_TOKEN set in Vercel's environment variables
// (Business Manager -> Data sources -> Datasets and pixels -> 2618965074964872
// -> Conversions API -> Set up manually -> Generate access token).

const PIXEL_ID = '2618965074964872';
const ALLOWED_EVENTS = new Set(['Lead', 'Contact']);

function sha256(value) {
  const crypto = require('crypto');
  return crypto.createHash('sha256').update(value.trim().toLowerCase()).digest('hex');
}

function getClientIp(req) {
  const fwd = req.headers['x-forwarded-for'];
  if (fwd) return fwd.split(',')[0].trim();
  return req.socket && req.socket.remoteAddress;
}

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', 'https://www.freemindconsult.com');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const token = process.env.META_CAPI_ACCESS_TOKEN;
  if (!token) {
    // Not configured yet -- fail quietly so the frontend never breaks the
    // actual lead flow waiting on this. Browser-side fbq() already fired.
    res.status(200).json({ skipped: true, reason: 'META_CAPI_ACCESS_TOKEN not set' });
    return;
  }

  let body;
  try {
    body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
  } catch (e) {
    res.status(400).json({ error: 'Invalid JSON body' });
    return;
  }

  const { eventName, eventId, eventSourceUrl, email, phone, externalId } = body || {};

  if (!eventName || !ALLOWED_EVENTS.has(eventName)) {
    res.status(400).json({ error: 'eventName must be one of: ' + [...ALLOWED_EVENTS].join(', ') });
    return;
  }
  if (!eventId) {
    res.status(400).json({ error: 'eventId is required (must match the browser fbq() call for dedup)' });
    return;
  }

  const userData = {
    client_ip_address: getClientIp(req),
    client_user_agent: req.headers['user-agent'] || '',
  };
  if (email) userData.em = [sha256(email)];
  if (phone) userData.ph = [sha256(phone.replace(/[^0-9]/g, ''))];
  if (externalId) userData.external_id = [sha256(externalId)];

  const payload = {
    data: [
      {
        event_name: eventName,
        event_time: Math.floor(Date.now() / 1000),
        event_id: eventId,
        event_source_url: eventSourceUrl || '',
        action_source: 'website',
        user_data: userData,
      },
    ],
  };

  try {
    const metaRes = await fetch(
      `https://graph.facebook.com/v25.0/${PIXEL_ID}/events?access_token=${encodeURIComponent(token)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }
    );
    const metaJson = await metaRes.json();
    if (!metaRes.ok) {
      res.status(502).json({ error: 'Meta CAPI rejected the event', detail: metaJson });
      return;
    }
    res.status(200).json({ ok: true, meta: metaJson });
  } catch (err) {
    res.status(502).json({ error: 'Failed to reach Meta CAPI', detail: String(err) });
  }
};
