# Payment Integration Expert (Python)

## Skill Identity
- **Name:** payment-integration-python
- **Version:** 1.0.0
- **Type:** Implementation Specialist
- **Language:** Python (Flask/Django/FastAPI)
- **Domain:** Payment Gateway Integration

---

## Purpose

Expert in integrating payment gateways (Stripe, Razorpay, PayPal, etc.) into Python applications with secure, production-ready implementations.

---

## Context7 Integration (CRITICAL!)

**ALWAYS use Context7 for latest payment gateway docs!**

### Before Any Implementation:

```bash
# Fetch latest docs via Context7
context7 search "Stripe Python SDK latest documentation"
context7 search "Razorpay Python integration guide 2026"
context7 search "PayPal Python SDK latest"
```

**Why Context7:**
- Payment APIs change frequently
- Security best practices evolve
- New features added regularly
- Deprecated methods need avoiding
- Compliance requirements update

**When to Use:**
1. Before implementing any payment gateway
2. When user mentions payment integration
3. For webhook implementation
4. For 3D Secure / PCI compliance
5. For latest SDK versions

---

## Supported Payment Gateways

### 1. Stripe (Most Popular)
**Use Cases:** International payments, subscriptions, SaaS
**Context7 Query:** `"Stripe Python SDK 2026 latest documentation"`

### 2. Razorpay (India)
**Use Cases:** Indian market, UPI, netbanking, cards
**Context7 Query:** `"Razorpay Python integration latest 2026"`

### 3. PayPal
**Use Cases:** Global payments, buyer protection
**Context7 Query:** `"PayPal Python SDK latest documentation"`

### 4. Square
**Use Cases:** Retail, POS integration
**Context7 Query:** `"Square Python SDK 2026 documentation"`

### 5. Braintree
**Use Cases:** Complex payment flows, vaulting
**Context7 Query:** `"Braintree Python SDK latest"`

---

## Implementation Workflow

### Step 1: Context7 Documentation Fetch

```python
# ALWAYS START WITH THIS!
# Use Context7 to get latest docs

from context7 import fetch_latest_docs

# Fetch latest SDK info
docs = fetch_latest_docs("Stripe Python SDK 2026")
sdk_version = docs.get_recommended_version()
best_practices = docs.get_security_guidelines()
```

### Step 2: Setup & Configuration

**Environment Variables (Never Hardcode!):**
```python
# .env file
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
```

**Configuration:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

STRIPE_CONFIG = {
    'secret_key': os.getenv('STRIPE_SECRET_KEY'),
    'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY'),
    'webhook_secret': os.getenv('STRIPE_WEBHOOK_SECRET')
}
```

### Step 3: Payment Intent Creation (Stripe Example)

```python
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)
stripe.api_key = STRIPE_CONFIG['secret_key']

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """
    Create payment intent with latest Stripe API
    Context7: Fetch latest payment intent creation method
    """
    try:
        data = request.get_json()

        # Create payment intent (check Context7 for latest params)
        intent = stripe.PaymentIntent.create(
            amount=data['amount'],  # in cents
            currency=data['currency'],
            automatic_payment_methods={'enabled': True},
            metadata={
                'order_id': data.get('order_id'),
                'user_id': data.get('user_id')
            }
        )

        return jsonify({
            'clientSecret': intent.client_secret,
            'intentId': intent.id
        }), 200

    except stripe.error.CardError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
```

### Step 4: Webhook Handling (CRITICAL for Security)

```python
@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """
    Verify and process Stripe webhooks
    Context7: Check latest webhook signature verification
    """
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = STRIPE_CONFIG['webhook_secret']

    try:
        # Verify webhook signature (SECURITY!)
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            handle_successful_payment(payment_intent)

        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            handle_failed_payment(payment_intent)

        elif event['type'] == 'charge.refunded':
            charge = event['data']['object']
            handle_refund(charge)

        return jsonify({'status': 'success'}), 200

    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
```

### Step 5: Razorpay Integration (India)

```python
import razorpay

client = razorpay.Client(auth=(
    os.getenv('RAZORPAY_KEY_ID'),
    os.getenv('RAZORPAY_KEY_SECRET')
))

@app.route('/create-razorpay-order', methods=['POST'])
def create_razorpay_order():
    """
    Create Razorpay order
    Context7: Fetch latest Razorpay order creation API
    """
    try:
        data = request.get_json()

        # Create order (Context7: check latest params)
        order = client.order.create({
            'amount': data['amount'],  # in paise
            'currency': 'INR',
            'receipt': data.get('receipt_id'),
            'notes': {
                'order_id': data.get('order_id'),
                'user_id': data.get('user_id')
            }
        })

        return jsonify(order), 200

    except razorpay.errors.BadRequestError as e:
        return jsonify({'error': str(e)}), 400
```

### Step 6: Payment Verification (Razorpay)

```python
@app.route('/verify-razorpay-payment', methods=['POST'])
def verify_razorpay_payment():
    """
    Verify Razorpay payment signature
    Context7: Latest signature verification method
    """
    try:
        data = request.get_json()

        # Verify signature (SECURITY!)
        params_dict = {
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        }

        client.utility.verify_payment_signature(params_dict)

        # Signature valid - process payment
        handle_successful_payment(data)

        return jsonify({'status': 'success'}), 200

    except razorpay.errors.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
```

---

## Security Best Practices (Context7: Latest Security Standards)

### 1. API Key Management
```python
# ✅ GOOD - Environment variables
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# ❌ BAD - Hardcoded
stripe.api_key = 'sk_live_xxxxx'  # NEVER DO THIS!
```

### 2. Webhook Signature Verification
```python
# ✅ ALWAYS verify webhook signatures
event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

# ❌ NEVER process webhooks without verification
```

### 3. Amount Validation
```python
# ✅ Validate amounts server-side
expected_amount = get_order_amount(order_id)
if payment_intent.amount != expected_amount:
    raise ValueError("Amount mismatch")
```

### 4. Idempotency
```python
# ✅ Use idempotency keys for retries
stripe.PaymentIntent.create(
    amount=1000,
    currency='usd',
    idempotency_key=f"payment_{order_id}"
)
```

---

## Error Handling (Context7: Latest Error Codes)

```python
import stripe

def process_payment(payment_data):
    """
    Comprehensive error handling
    Context7: Check latest Stripe error types
    """
    try:
        intent = stripe.PaymentIntent.create(**payment_data)
        return {'success': True, 'data': intent}

    except stripe.error.CardError as e:
        # Card declined
        return {'success': False, 'error': 'card_declined', 'message': str(e)}

    except stripe.error.RateLimitError:
        # Too many requests
        return {'success': False, 'error': 'rate_limit'}

    except stripe.error.InvalidRequestError as e:
        # Invalid parameters
        return {'success': False, 'error': 'invalid_request', 'message': str(e)}

    except stripe.error.AuthenticationError:
        # Authentication failed
        return {'success': False, 'error': 'auth_failed'}

    except stripe.error.APIConnectionError:
        # Network error
        return {'success': False, 'error': 'network_error'}

    except stripe.error.StripeError as e:
        # Generic Stripe error
        return {'success': False, 'error': 'stripe_error', 'message': str(e)}

    except Exception as e:
        # Unexpected error
        return {'success': False, 'error': 'internal_error'}
```

---

## Testing (Context7: Latest Test Cards)

### Stripe Test Cards
```python
# Context7: Fetch latest test card numbers

TEST_CARDS = {
    'success': '4242424242424242',
    'decline': '4000000000000002',
    '3d_secure': '4000002500003155',
    'insufficient_funds': '4000000000009995'
}
```

### Test Payment Flow
```python
import pytest

@pytest.fixture
def stripe_mock():
    # Mock Stripe for testing
    import stripe
    stripe.api_key = 'sk_test_xxxxx'
    return stripe

def test_create_payment_intent(stripe_mock):
    """Test payment intent creation"""
    intent = stripe_mock.PaymentIntent.create(
        amount=1000,
        currency='usd'
    )
    assert intent.status == 'requires_payment_method'
```

---

## Django Integration

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

@require_http_methods(["POST"])
def create_payment_intent(request):
    """
    Django view for payment intent
    Context7: Latest Django + Stripe integration
    """
    try:
        import json
        data = json.loads(request.body)

        intent = stripe.PaymentIntent.create(
            amount=data['amount'],
            currency=data['currency'],
            metadata={'user_id': request.user.id}
        )

        return JsonResponse({
            'clientSecret': intent.client_secret
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt  # Stripe webhooks need this
@require_http_methods(["POST"])
def stripe_webhook(request):
    """Handle Stripe webhooks in Django"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        # Process event...
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
```

---

## FastAPI Integration

```python
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import stripe

app = FastAPI()
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str
    order_id: str

@app.post("/create-payment-intent")
async def create_payment_intent(payment: PaymentIntentRequest):
    """
    FastAPI payment intent endpoint
    Context7: Latest FastAPI + Stripe patterns
    """
    try:
        intent = stripe.PaymentIntent.create(
            amount=payment.amount,
            currency=payment.currency,
            metadata={'order_id': payment.order_id}
        )
        return {"clientSecret": intent.client_secret}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/webhook")
async def stripe_webhook(request: Request):
    """FastAPI webhook handler"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        # Process event...
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Subscription Handling (Context7: Latest Subscription APIs)

```python
@app.route('/create-subscription', methods=['POST'])
def create_subscription():
    """
    Create recurring subscription
    Context7: Latest Stripe Subscriptions API
    """
    try:
        data = request.get_json()

        # Create customer first
        customer = stripe.Customer.create(
            email=data['email'],
            payment_method=data['payment_method_id'],
            invoice_settings={
                'default_payment_method': data['payment_method_id']
            }
        )

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': data['price_id']}],
            expand=['latest_invoice.payment_intent']
        )

        return jsonify({
            'subscriptionId': subscription.id,
            'clientSecret': subscription.latest_invoice.payment_intent.client_secret
        }), 200

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
```

---

## Refund Handling

```python
@app.route('/refund', methods=['POST'])
def refund_payment():
    """
    Process refund
    Context7: Latest refund policies and API
    """
    try:
        data = request.get_json()

        refund = stripe.Refund.create(
            payment_intent=data['payment_intent_id'],
            amount=data.get('amount'),  # Optional partial refund
            reason=data.get('reason', 'requested_by_customer')
        )

        return jsonify({
            'refundId': refund.id,
            'status': refund.status
        }), 200

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
```

---

## Context7 Query Examples

**Before implementing any feature, use Context7:**

```python
# Example 1: Payment Intent
context7_query("Stripe Python PaymentIntent create 2026 latest API")

# Example 2: Webhooks
context7_query("Stripe webhook signature verification Python best practices 2026")

# Example 3: 3D Secure
context7_query("Stripe 3D Secure 2 Python implementation latest")

# Example 4: Razorpay UPI
context7_query("Razorpay UPI Python integration latest documentation")

# Example 5: PayPal Checkout
context7_query("PayPal Checkout Python SDK v2 latest 2026")
```

---

## When to Use This Skill

✅ User mentions payment integration
✅ Need to implement checkout flow
✅ Webhook setup required
✅ Subscription/recurring billing
✅ Refund processing
✅ Payment gateway comparison
✅ PCI compliance questions

---

## Execution Checklist

**ALWAYS follow this order:**

1. ✅ **Context7 Query** - Fetch latest docs
2. ✅ **Security Check** - Verify environment variables
3. ✅ **Webhook Verification** - Implement signature check
4. ✅ **Error Handling** - Comprehensive try-catch
5. ✅ **Testing** - Use test mode first
6. ✅ **Logging** - Log all payment events
7. ✅ **Documentation** - Comment security-critical parts

---

## Common Pitfalls (Avoid These!)

❌ Hardcoding API keys
❌ Skipping webhook verification
❌ Not handling errors properly
❌ Using old SDK versions
❌ Ignoring idempotency
❌ Client-side amount validation only
❌ Not logging payment events

---

## Status

**Version:** 1.0.0
**Context7 Integration:** MANDATORY
**Security Level:** HIGH
**Production Ready:** ✅

---

**Remember:** ALWAYS use Context7 before implementing any payment feature!
Payment APIs change frequently - stay updated! 🚀
