# Stripe Billing Integration

## 1. Setup

```bash
pip install stripe flask python-dotenv
```

## 2. Environment Variables

```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
WEBHOOK_SECRET=whsec_...
```

## 3. Python Backend

```python
import stripe
from flask import Flask, request, jsonify
import os

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
app = Flask(__name__)

# Create subscription
@app.route('/create-subscription', methods=['POST'])
def create_subscription():
    data = request.json
    customer = stripe.Customer.create(
        email=data['email'],
        payment_method=data['payment_method_id'],
        invoice_settings={'default_payment_method': data['payment_method_id']}
    )

    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[{
            'price': data['price_id']  # e.g., 'price_professional' or 'price_enterprise'
        }],
        expand=['latest_invoice.payment_intent']
    )

    return jsonify({
        'subscriptionId': subscription.id,
        'clientSecret': subscription.latest_invoice.payment_intent.client_secret
    })

# Webhook handler
@app.route('/webhook', methods=['POST'])
def webhook():
    sig_header = request.headers.get('stripe-signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            request.data, sig_header, os.getenv('WEBHOOK_SECRET')
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400

    # Handle events
    if event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        # Update user subscription status in DB
        update_user_subscription(subscription['customer'], subscription)

    elif event['type'] == 'invoice.payment_succeeded':
        # Send receipt email
        pass

    elif event['type'] == 'customer.subscription.deleted':
        # Handle cancellation
        pass

    return 'Success', 200

def update_user_subscription(customer_id, subscription):
    # Your DB update logic
    status = subscription['status']  # 'active', 'past_due', 'canceled', etc.
    price_id = subscription['items']['data'][0]['price']['id']
    tier = price_id.split('_')[1]  # 'free', 'professional', 'enterprise'
    # Update user record with tier and status
```

## 4. Frontend - Payment Form

```html
<script src="https://js.stripe.com/v3/"></script>
<form id="payment-form">
  <div id="card-element"></div>
  <button type="submit">Subscribe ($99/month)</button>
</form>

<script>
const stripe = Stripe('pk_live_...');
const elements = stripe.elements();
const cardElement = elements.create('card');
cardElement.mount('#card-element');

document.getElementById('payment-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const {paymentMethod} = await stripe.createPaymentMethod({
    type: 'card',
    card: cardElement,
    billing_details: { email: 'user@example.com' }
  });

  const response = await fetch('/create-subscription', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'user@example.com',
      payment_method_id: paymentMethod.id,
      price_id: 'price_professional'
    })
  });

  const {subscriptionId} = await response.json();
  // Handle success/redirect
});
</script>
```

## 5. Price IDs

Create in Stripe Dashboard:
- `price_free`: $0/month (manual setup)
- `price_professional`: $99/month (recurring)
- `price_enterprise`: Custom amount (contact sales)

## 6. Customer Portal

```python
@app.route('/billing-portal', methods=['POST'])
def billing_portal():
    customer_id = request.json['customer_id']
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url='https://autonomous-agent.dev/dashboard'
    )
    return jsonify({'url': session.url})
```

## 7. Usage-Based Billing (API Overage)

```python
def record_api_usage(customer_id, units):
    """Record API usage for overage charges"""
    stripe.SubscriptionItem.create_usage_record(
        id='si_...',  # subscription_item_id
        quantity=units
    )

# Set price with metered billing
stripe.Product.create(
    name='API Calls',
    type='service',
    billing_scheme='tiered',
    tiers=[
        {'up_to': 10000, 'unit_amount': 0},  # Included
        {'up_to_inf': True, 'unit_amount': 1}  # $0.01 per call
    ]
)
```

## 8. Dunning - Failed Payment Recovery

Stripe handles automatically with:
- 3 retry attempts
- Customizable email templates
- Webhook notifications

## 9. Testing

Test cards:
- Success: 4242 4242 4242 4242
- Declined: 4000 0000 0000 0002
- 3D Secure: 4000 0025 0000 3155

```bash
stripe listen --forward-to localhost:5000/webhook
```

## 10. Production Checklist

- [ ] Use live API keys (not test)
- [ ] Enable 3D Secure authentication
- [ ] Configure webhook signing verification
- [ ] Set up email notifications
- [ ] Test payment failure scenarios
- [ ] Implement idempotency keys
- [ ] Add rate limiting
- [ ] Set up fraud prevention
