# Payment Integration Skills - Complete Guide

## Overview

**Three specialized skills for payment gateway integration across Python, Java, and TypeScript.**

All skills include **mandatory Context7 integration** for fetching latest documentation.

---

## Available Skills

### 1. payment-integration-python
**File:** `payment-integration-python.md`
**Language:** Python (Flask/Django/FastAPI)
**Size:** 621 lines
**Gateways:** Stripe, Razorpay, PayPal, Square, Braintree

**Key Features:**
- ✅ Flask, Django, FastAPI implementations
- ✅ Context7 integration for latest docs
- ✅ Webhook signature verification
- ✅ Comprehensive error handling
- ✅ Test card examples
- ✅ Subscription handling
- ✅ Refund processing

---

### 2. payment-integration-java
**File:** `payment-integration-java.md`
**Language:** Java (Spring Boot)
**Size:** 774 lines
**Gateways:** Stripe, Razorpay, PayPal, Square, Braintree

**Key Features:**
- ✅ Spring Boot REST controllers
- ✅ Context7 integration
- ✅ Type-safe DTOs
- ✅ Service layer architecture
- ✅ Webhook handling with signature verification
- ✅ Exception handling
- ✅ Maven dependencies
- ✅ Comprehensive testing

---

### 3. payment-integration-typescript
**File:** `payment-integration-typescript.md`
**Language:** TypeScript/Node.js (Express/NestJS)
**Size:** 902 lines (largest!)
**Gateways:** Stripe, Razorpay, PayPal, Square, Braintree

**Key Features:**
- ✅ Express & NestJS implementations
- ✅ Full TypeScript type safety
- ✅ Context7 integration
- ✅ Zod validation
- ✅ Webhook signature verification
- ✅ Comprehensive error types
- ✅ Jest testing examples
- ✅ Environment configuration

---

## Context7 Integration (CRITICAL!)

### What is Context7?

**Context7 = Always fetch latest docs before implementation!**

### Why Mandatory?

Payment APIs change frequently:
- 📚 New SDK versions released
- 🔒 Security patches
- 🚨 Deprecated methods
- ✨ New features
- 📋 Updated compliance requirements

### Usage Pattern

**Before implementing ANY payment feature:**

```python
# Python
context7.search("Stripe Python SDK 2026 latest documentation")
context7.search("Razorpay Python integration latest")
```

```java
// Java
context7.search("Stripe Java SDK Spring Boot 2026 latest");
context7.search("Razorpay Java integration latest");
```

```typescript
// TypeScript
await context7.search("Stripe TypeScript SDK 2026 latest");
await context7.search("Razorpay TypeScript Node.js latest");
```

### When to Use Context7

1. ✅ **Before implementation** - Verify latest API
2. ✅ **During errors** - Check updated error codes
3. ✅ **For webhooks** - Latest signature verification
4. ✅ **For 3D Secure** - Current implementation
5. ✅ **For subscriptions** - Latest billing APIs
6. ✅ **For refunds** - Updated refund policies

---

## Supported Payment Gateways

All three skills support:

### 1. Stripe (Global Leader)
**Best For:** International payments, SaaS, subscriptions
**Coverage:** All 3 skills (primary focus)

### 2. Razorpay (India)
**Best For:** Indian market, UPI, netbanking, cards
**Coverage:** All 3 skills (India-specific examples)

### 3. PayPal (Global)
**Best For:** Buyer protection, global reach
**Coverage:** All 3 skills (SDK v2)

### 4. Square (US/UK)
**Best For:** Retail, POS integration
**Coverage:** Mentioned in all 3 skills

### 5. Braintree (PayPal-owned)
**Best For:** Complex payment flows
**Coverage:** Mentioned in all 3 skills

---

## Common Implementation Pattern

### All skills follow this workflow:

```
1. Context7 Documentation Fetch
   ↓
2. Configuration Setup (env variables)
   ↓
3. Payment Intent/Order Creation
   ↓
4. Webhook Signature Verification (SECURITY!)
   ↓
5. Error Handling (comprehensive)
   ↓
6. Testing (test mode)
   ↓
7. Production Deployment
```

---

## Security Features (ALL Skills)

### ✅ Mandatory Security Practices:

1. **API Key Management**
   - Environment variables (NEVER hardcoded)
   - Separate test/live keys
   - Rotation policies

2. **Webhook Verification**
   - Signature verification (ALWAYS!)
   - HMAC validation
   - Timestamp checking

3. **Amount Validation**
   - Server-side validation
   - No client-side trust
   - Order amount matching

4. **HTTPS Only**
   - SSL/TLS required
   - No plaintext transmission

5. **Idempotency**
   - Idempotency keys for retries
   - Prevent duplicate charges

6. **Logging**
   - All payment events logged
   - Audit trail maintained
   - No sensitive data in logs

7. **Error Handling**
   - Graceful degradation
   - User-friendly messages
   - Detailed internal logs

---

## Quick Start Examples

### Python (Flask)

```python
from flask import Flask, request
import stripe

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@app.route('/create-payment', methods=['POST'])
def create_payment():
    intent = stripe.PaymentIntent.create(
        amount=1000,
        currency='usd'
    )
    return {'clientSecret': intent.client_secret}
```

### Java (Spring Boot)

```java
@RestController
public class PaymentController {

    @PostMapping("/create-payment")
    public ResponseEntity<?> createPayment(@RequestBody PaymentRequest request) {
        PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
            .setAmount(request.getAmount())
            .setCurrency(request.getCurrency())
            .build();

        PaymentIntent intent = PaymentIntent.create(params);

        return ResponseEntity.ok(Map.of("clientSecret", intent.getClientSecret()));
    }
}
```

### TypeScript (Express)

```typescript
import express from 'express';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

app.post('/create-payment', async (req, res) => {
  const intent = await stripe.paymentIntents.create({
    amount: 1000,
    currency: 'usd',
  });

  res.json({ clientSecret: intent.client_secret });
});
```

---

## Skill Selection Guide

### When to Use Each Skill

**Use Python Skill If:**
- ✅ Backend in Python (Flask/Django/FastAPI)
- ✅ Data science/ML integration needed
- ✅ Rapid prototyping required
- ✅ Simple syntax preferred

**Use Java Skill If:**
- ✅ Spring Boot application
- ✅ Enterprise environment
- ✅ Strong typing required
- ✅ Microservices architecture
- ✅ Large-scale system

**Use TypeScript Skill If:**
- ✅ Node.js backend (Express/NestJS)
- ✅ Full-stack TypeScript
- ✅ Modern async/await patterns
- ✅ Frontend + backend integration
- ✅ Type safety without JVM overhead

---

## Common Features Across All Skills

### ✅ Implemented in All:

1. **Payment Intent Creation**
   - Create payment
   - Retrieve payment
   - Update payment

2. **Webhook Handling**
   - Signature verification
   - Event processing
   - Success/failure handling

3. **Refund Processing**
   - Full refunds
   - Partial refunds
   - Refund reasons

4. **Error Handling**
   - Card declined
   - Network errors
   - Invalid requests
   - Authentication failures
   - Rate limits

5. **Testing**
   - Test cards
   - Test mode
   - Unit tests
   - Mocking examples

6. **Subscription Support**
   - Create subscription
   - Cancel subscription
   - Update subscription

---

## Context7 Query Examples

### Universal Queries (All Languages)

```
# Latest SDK Versions
"[Gateway] [Language] SDK 2026 latest version"

# Webhook Verification
"[Gateway] webhook signature verification [Language] best practices"

# 3D Secure
"[Gateway] 3D Secure 2 [Language] implementation latest"

# Error Handling
"[Gateway] [Language] error types latest documentation"

# Subscriptions
"[Gateway] subscription billing [Language] SDK latest"
```

### Specific Examples

```
# Stripe Python
"Stripe Python SDK 2026 PaymentIntent latest API"

# Razorpay Java
"Razorpay Java SDK Spring Boot integration latest"

# PayPal TypeScript
"PayPal TypeScript SDK REST API v2 latest 2026"
```

---

## Testing Strategy

### All Skills Include:

1. **Test Mode**
   - Separate test API keys
   - Test card numbers
   - Test webhooks

2. **Unit Tests**
   - Service layer tests
   - Mock external APIs
   - Error scenario tests

3. **Integration Tests**
   - End-to-end flows
   - Webhook handling
   - Database integration

4. **Test Cards**
   - Success: `4242424242424242`
   - Decline: `4000000000000002`
   - 3D Secure: `4000002500003155`

---

## Webhook Event Types

### Common Events (All Gateways)

1. **Payment Events**
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.captured`
   - `charge.refunded`

2. **Subscription Events**
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

3. **Customer Events**
   - `customer.created`
   - `customer.updated`

---

## Production Checklist

### Before Going Live:

- [ ] Replace test API keys with live keys
- [ ] Test webhook endpoints
- [ ] Set up monitoring
- [ ] Configure error alerting
- [ ] Enable logging
- [ ] Review security practices
- [ ] Test refund flow
- [ ] Verify HTTPS
- [ ] Set up rate limiting
- [ ] Document payment flow

---

## File Locations

```
~/.claude/skills/
├── payment-integration-python.md       (621 lines)
├── payment-integration-java.md         (774 lines)
├── payment-integration-typescript.md   (902 lines)
└── PAYMENT-INTEGRATION-GUIDE.md        (this file)
```

---

## When to Use These Skills

### Trigger Keywords:

✅ "payment integration"
✅ "checkout implementation"
✅ "Stripe/Razorpay/PayPal integration"
✅ "webhook setup"
✅ "subscription billing"
✅ "refund processing"
✅ "payment gateway"

### User Mentions:

- Python + payment → Use Python skill
- Java/Spring Boot + payment → Use Java skill
- TypeScript/Node.js + payment → Use TypeScript skill

---

## Integration with Other Systems

### Works Well With:

1. **Session Memory** - Remember payment preferences
2. **Failure Learning** - Learn from payment errors
3. **Context Management** - Smart cleanup of payment context
4. **Logging System** - Track payment events

---

## Stats

```
Total Skills: 3
Total Lines: 2,297 lines
Languages: Python, Java, TypeScript
Gateways: 5 (Stripe, Razorpay, PayPal, Square, Braintree)
Context7 Integration: 100% (all skills)
Security Level: HIGH
Production Ready: ✅
```

---

## Support Matrix

| Feature | Python | Java | TypeScript |
|---------|--------|------|------------|
| Stripe | ✅ | ✅ | ✅ |
| Razorpay | ✅ | ✅ | ✅ |
| PayPal | ✅ | ✅ | ✅ |
| Webhooks | ✅ | ✅ | ✅ |
| Refunds | ✅ | ✅ | ✅ |
| Subscriptions | ✅ | ✅ | ✅ |
| 3D Secure | ✅ | ✅ | ✅ |
| Testing | ✅ | ✅ | ✅ |
| Context7 | ✅ | ✅ | ✅ |

---

## Version

**Version:** 1.0.0
**Created:** 2026-01-26
**Status:** Production Ready
**Context7:** Mandatory for all implementations

---

## Quick Reference

**Remember:**
1. ✅ Always use Context7 before implementing
2. ✅ Verify webhook signatures (SECURITY!)
3. ✅ Handle errors comprehensively
4. ✅ Test in test mode first
5. ✅ Never hardcode API keys
6. ✅ Log all payment events
7. ✅ Use idempotency keys

---

**Payment APIs change frequently - Context7 keeps you updated! 🚀**
