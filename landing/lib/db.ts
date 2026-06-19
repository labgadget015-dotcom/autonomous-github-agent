import { sql } from "@vercel/postgres";

export async function ensureSchema() {
  await sql`
    CREATE TABLE IF NOT EXISTS subscriptions (
      id              SERIAL PRIMARY KEY,
      customer_id     TEXT NOT NULL UNIQUE,
      subscription_id TEXT NOT NULL UNIQUE,
      customer_email  TEXT,
      status          TEXT NOT NULL DEFAULT 'active',
      tier            TEXT NOT NULL DEFAULT 'growth',
      created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
}

export async function upsertSubscription(params: {
  customerId: string;
  subscriptionId: string;
  customerEmail?: string | null;
  status: string;
  tier: string;
}) {
  await sql`
    INSERT INTO subscriptions (customer_id, subscription_id, customer_email, status, tier)
    VALUES (${params.customerId}, ${params.subscriptionId}, ${params.customerEmail ?? null}, ${params.status}, ${params.tier})
    ON CONFLICT (customer_id) DO UPDATE SET
      subscription_id = EXCLUDED.subscription_id,
      customer_email  = COALESCE(EXCLUDED.customer_email, subscriptions.customer_email),
      status          = EXCLUDED.status,
      tier            = EXCLUDED.tier,
      updated_at      = NOW()
  `;
}

export async function updateSubscriptionStatus(customerId: string, status: string) {
  await sql`
    UPDATE subscriptions SET status = ${status}, updated_at = NOW()
    WHERE customer_id = ${customerId}
  `;
}

export async function getSubscriptionByEmail(email: string) {
  const result = await sql`
    SELECT * FROM subscriptions WHERE customer_email = ${email} LIMIT 1
  `;
  return result.rows[0] ?? null;
}
