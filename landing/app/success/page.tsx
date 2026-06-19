import { redirect } from "next/navigation";
import Stripe from "stripe";
import Link from "next/link";

function getStripe() {
  return new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: "2025-02-24.acacia" });
}

export default async function SuccessPage({
  searchParams,
}: {
  searchParams: { session_id?: string };
}) {
  const sessionId = searchParams.session_id;
  if (!sessionId) redirect("/");

  let email: string | null = null;
  let name: string | null = null;

  try {
    const stripe = getStripe();
    const session = await stripe.checkout.sessions.retrieve(sessionId, {
      expand: ["customer_details"],
    });
    email = session.customer_details?.email ?? null;
    name = session.customer_details?.name ?? null;
  } catch {
    redirect("/");
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-brand-50 to-white flex items-center justify-center px-4">
      <div className="max-w-lg w-full text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-3xl font-extrabold text-gray-900 mb-3">
          You&apos;re in!
        </h1>
        {name && (
          <p className="text-gray-500 mb-1">Welcome, {name}.</p>
        )}
        {email && (
          <p className="text-gray-500 mb-6">
            Confirmation sent to <strong>{email}</strong>.
          </p>
        )}

        <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-8 text-left space-y-4">
          <h2 className="font-semibold text-gray-900">What happens next</h2>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-brand-100 text-brand-700 rounded-full flex items-center justify-center font-bold text-xs">1</span>
              <span>Your GadgetLab Agent instance is being provisioned — ready in ~60 seconds.</span>
            </div>
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-brand-100 text-brand-700 rounded-full flex items-center justify-center font-bold text-xs">2</span>
              <span>Check your email for setup instructions and your n8n webhook URL.</span>
            </div>
            <div className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-brand-100 text-brand-700 rounded-full flex items-center justify-center font-bold text-xs">3</span>
              <span>Add the webhook to your GitHub repo and the DRC pipeline goes live.</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/dashboard"
            className="bg-brand-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-brand-700 transition-colors"
          >
            Go to dashboard
          </Link>
          <a
            href="https://github.com/labgadget015-dotcom/autonomous-github-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="border border-gray-300 text-gray-700 px-6 py-3 rounded-xl font-semibold hover:border-gray-400 transition-colors bg-white"
          >
            View docs on GitHub
          </a>
        </div>

        <p className="mt-8 text-sm text-gray-400">
          Questions? Email{" "}
          <a href="mailto:labgadget015@gmail.com" className="text-brand-600 hover:underline">
            labgadget015@gmail.com
          </a>
        </p>
      </div>
    </main>
  );
}
