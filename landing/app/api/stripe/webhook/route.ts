import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import { upsertSubscription, updateSubscriptionStatus, ensureSchema } from "@/lib/db";

// Initialized lazily so the build succeeds without STRIPE_SECRET_KEY set
let _stripe: Stripe | null = null;
function getStripe(): Stripe {
  if (!_stripe) {
    _stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: "2025-02-24.acacia" });
  }
  return _stripe;
}

// Ensure the subscriptions table exists once per cold start
let _schemaReady: Promise<void> | null = null;
function ensureSchemaOnce(): Promise<void> {
  if (!_schemaReady) _schemaReady = ensureSchema();
  return _schemaReady;
}

export async function POST(req: NextRequest) {
  await ensureSchemaOnce();
  const body = await req.text();
  const sig = req.headers.get("stripe-signature");

  if (!sig) {
    return NextResponse.json({ error: "Missing stripe-signature header" }, { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = getStripe().webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Webhook signature verification failed";
    console.error("Stripe webhook error:", msg);
    return NextResponse.json({ error: msg }, { status: 400 });
  }

  try {
    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;
        await handleCheckoutComplete(session);
        break;
      }
      case "customer.subscription.updated": {
        const sub = event.data.object as Stripe.Subscription;
        await handleSubscriptionUpdate(sub);
        break;
      }
      case "customer.subscription.deleted": {
        const sub = event.data.object as Stripe.Subscription;
        await handleSubscriptionCancelled(sub);
        break;
      }
      case "invoice.payment_failed": {
        const invoice = event.data.object as Stripe.Invoice;
        await handlePaymentFailed(invoice);
        break;
      }
      default:
        console.log(`Unhandled Stripe event: ${event.type}`);
    }
  } catch (err) {
    console.error(`Error handling ${event.type}:`, err);
    return NextResponse.json({ error: "Handler failed" }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}

async function handleCheckoutComplete(session: Stripe.Checkout.Session) {
  const customerId = session.customer as string;
  const customerEmail = session.customer_details?.email;
  const subscriptionId = session.subscription as string;

  console.log(`✅ New subscription: customer=${customerId} email=${customerEmail} sub=${subscriptionId}`);

  await upsertSubscription({ customerId, subscriptionId, customerEmail, status: "active", tier: "growth" });

  // Notify via n8n webhook for downstream automation (DRC analysis of new customer)
  await notifyN8n("subscription.created", { customerId, customerEmail, subscriptionId });
}

async function handleSubscriptionUpdate(sub: Stripe.Subscription) {
  console.log(`🔄 Subscription updated: sub=${sub.id} status=${sub.status}`);
  await updateSubscriptionStatus(sub.customer as string, sub.status);
}

async function handleSubscriptionCancelled(sub: Stripe.Subscription) {
  const customerId = sub.customer as string;
  console.log(`❌ Subscription cancelled: customer=${customerId} sub=${sub.id}`);

  await updateSubscriptionStatus(customerId, "cancelled");

  await notifyN8n("subscription.cancelled", { customerId, subscriptionId: sub.id });
}

async function handlePaymentFailed(invoice: Stripe.Invoice) {
  const customerId = invoice.customer as string;
  const attemptCount = invoice.attempt_count;
  console.log(`⚠️ Payment failed: customer=${customerId} attempt=${attemptCount}`);
  await updateSubscriptionStatus(customerId, "past_due");
}

async function notifyN8n(event: string, payload: Record<string, unknown>) {
  const webhookUrl = process.env.N8N_STRIPE_WEBHOOK_URL;
  if (!webhookUrl) return;

  try {
    await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event, ...payload, timestamp: new Date().toISOString() }),
    });
  } catch (err) {
    console.error("Failed to notify n8n:", err);
  }
}
