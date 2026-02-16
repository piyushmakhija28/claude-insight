# Payment Integration Expert (TypeScript/Node.js)

## Skill Identity
- **Name:** payment-integration-typescript
- **Version:** 1.0.0
- **Type:** Implementation Specialist
- **Language:** TypeScript/Node.js (Express/NestJS)
- **Domain:** Payment Gateway Integration

---

## Purpose

Expert in integrating payment gateways (Stripe, Razorpay, PayPal, etc.) into TypeScript/Node.js applications with type-safe, secure, production-ready implementations.

---

## Context7 Integration (CRITICAL!)

**ALWAYS use Context7 for latest payment gateway docs!**

### Before Any Implementation:

```typescript
// Fetch latest docs via Context7
await context7.search("Stripe TypeScript SDK latest documentation 2026");
await context7.search("Razorpay Node.js TypeScript integration latest");
await context7.search("PayPal TypeScript SDK latest 2026");
```

**Why Context7:**
- Payment SDKs update frequently
- TypeScript types change with API versions
- Security patches released regularly
- Best practices evolve
- Compliance requirements update

**When to Use:**
1. Before implementing any payment gateway
2. When setting up webhooks
3. For type definitions
4. For error handling patterns
5. For latest security practices
6. When SDK errors occur

---

## Supported Payment Gateways

### 1. Stripe (Most Popular)
**Use Cases:** Global payments, subscriptions, SaaS
**Context7 Query:** `"Stripe TypeScript SDK 2026 latest documentation"`

### 2. Razorpay (India)
**Use Cases:** Indian market, UPI, cards, netbanking
**Context7 Query:** `"Razorpay TypeScript Node.js integration latest"`

### 3. PayPal
**Use Cases:** Global payments, buyer protection
**Context7 Query:** `"PayPal TypeScript SDK REST API latest"`

### 4. Square
**Use Cases:** Retail, POS
**Context7 Query:** `"Square TypeScript SDK latest documentation"`

### 5. Braintree
**Use Cases:** Complex payment flows
**Context7 Query:** `"Braintree TypeScript SDK latest"`

---

## Package Installation

```bash
# Stripe
npm install stripe
npm install @types/stripe --save-dev

# Razorpay
npm install razorpay
npm install @types/razorpay --save-dev

# PayPal
npm install @paypal/checkout-server-sdk

# Express
npm install express
npm install @types/express --save-dev

# Environment variables
npm install dotenv

# Validation
npm install zod  # or joi, yup
```

```json
// package.json
{
  "dependencies": {
    "stripe": "^14.10.0",
    "razorpay": "^2.9.2",
    "@paypal/checkout-server-sdk": "^1.0.3",
    "express": "^4.18.2",
    "dotenv": "^16.3.1",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^20.10.0",
    "typescript": "^5.3.3",
    "ts-node": "^10.9.2"
  }
}
```

---

## TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

---

## Environment Configuration

```typescript
// src/config/env.ts
import { z } from 'zod';
import dotenv from 'dotenv';

dotenv.config();

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().default('3000'),

  // Stripe
  STRIPE_SECRET_KEY: z.string(),
  STRIPE_PUBLISHABLE_KEY: z.string(),
  STRIPE_WEBHOOK_SECRET: z.string(),

  // Razorpay
  RAZORPAY_KEY_ID: z.string(),
  RAZORPAY_KEY_SECRET: z.string(),

  // PayPal
  PAYPAL_CLIENT_ID: z.string(),
  PAYPAL_CLIENT_SECRET: z.string(),
  PAYPAL_MODE: z.enum(['sandbox', 'live']).default('sandbox'),
});

export const env = envSchema.parse(process.env);

// Type-safe environment
export type Env = z.infer<typeof envSchema>;
```

```env
# .env
NODE_ENV=development
PORT=3000

# Stripe
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx

# PayPal
PAYPAL_CLIENT_ID=xxxxx
PAYPAL_CLIENT_SECRET=xxxxx
PAYPAL_MODE=sandbox
```

---

## Stripe Implementation (Express + TypeScript)

### 1. Types & Interfaces

```typescript
// src/types/payment.types.ts
import Stripe from 'stripe';

export interface PaymentIntentRequest {
  amount: number;
  currency: string;
  orderId: string;
  userId: string;
  description?: string;
}

export interface PaymentIntentResponse {
  clientSecret: string;
  intentId: string;
}

export interface RefundRequest {
  paymentIntentId: string;
  amount?: number;
  reason?: 'duplicate' | 'fraudulent' | 'requested_by_customer';
}

export interface RefundResponse {
  refundId: string;
  status: string;
  amount: number;
}

export interface WebhookEvent {
  type: string;
  data: {
    object: any;
  };
}
```

### 2. Stripe Service

```typescript
// src/services/stripe.service.ts
import Stripe from 'stripe';
import { env } from '../config/env';
import type {
  PaymentIntentRequest,
  PaymentIntentResponse,
  RefundRequest,
  RefundResponse
} from '../types/payment.types';

export class StripeService {
  private stripe: Stripe;

  constructor() {
    // Context7: Check latest Stripe initialization
    this.stripe = new Stripe(env.STRIPE_SECRET_KEY, {
      apiVersion: '2023-10-16', // Context7: Use latest API version
      typescript: true,
    });
  }

  /**
   * Create Payment Intent
   * Context7: Latest PaymentIntent API parameters
   */
  async createPaymentIntent(
    request: PaymentIntentRequest
  ): Promise<PaymentIntentResponse> {
    try {
      const paymentIntent = await this.stripe.paymentIntents.create({
        amount: request.amount, // in cents
        currency: request.currency,
        automatic_payment_methods: { enabled: true },
        metadata: {
          orderId: request.orderId,
          userId: request.userId,
        },
        description: request.description,
      });

      return {
        clientSecret: paymentIntent.client_secret!,
        intentId: paymentIntent.id,
      };
    } catch (error) {
      throw this.handleStripeError(error);
    }
  }

  /**
   * Retrieve Payment Intent
   */
  async getPaymentIntent(intentId: string): Promise<Stripe.PaymentIntent> {
    try {
      return await this.stripe.paymentIntents.retrieve(intentId);
    } catch (error) {
      throw this.handleStripeError(error);
    }
  }

  /**
   * Process Refund
   * Context7: Latest refund API
   */
  async createRefund(request: RefundRequest): Promise<RefundResponse> {
    try {
      const refund = await this.stripe.refunds.create({
        payment_intent: request.paymentIntentId,
        amount: request.amount,
        reason: request.reason,
      });

      return {
        refundId: refund.id,
        status: refund.status,
        amount: refund.amount,
      };
    } catch (error) {
      throw this.handleStripeError(error);
    }
  }

  /**
   * Verify Webhook Signature (CRITICAL!)
   * Context7: Latest signature verification
   */
  constructWebhookEvent(
    payload: string | Buffer,
    signature: string
  ): Stripe.Event {
    try {
      return this.stripe.webhooks.constructEvent(
        payload,
        signature,
        env.STRIPE_WEBHOOK_SECRET
      );
    } catch (error) {
      throw new Error(`Webhook signature verification failed: ${error}`);
    }
  }

  /**
   * Handle Stripe errors with proper typing
   */
  private handleStripeError(error: unknown): Error {
    if (error instanceof Stripe.errors.StripeCardError) {
      return new Error(`Card error: ${error.message}`);
    } else if (error instanceof Stripe.errors.StripeRateLimitError) {
      return new Error('Rate limit exceeded');
    } else if (error instanceof Stripe.errors.StripeInvalidRequestError) {
      return new Error(`Invalid request: ${error.message}`);
    } else if (error instanceof Stripe.errors.StripeAPIError) {
      return new Error(`Stripe API error: ${error.message}`);
    } else if (error instanceof Stripe.errors.StripeConnectionError) {
      return new Error('Network error');
    } else if (error instanceof Stripe.errors.StripeAuthenticationError) {
      return new Error('Authentication failed');
    }
    return new Error('Unknown error occurred');
  }
}
```

### 3. Payment Controller

```typescript
// src/controllers/payment.controller.ts
import { Request, Response, NextFunction } from 'express';
import { StripeService } from '../services/stripe.service';
import { z } from 'zod';

// Request validation schemas
const PaymentIntentSchema = z.object({
  amount: z.number().positive(),
  currency: z.string().length(3),
  orderId: z.string(),
  userId: z.string(),
  description: z.string().optional(),
});

export class PaymentController {
  private stripeService: StripeService;

  constructor() {
    this.stripeService = new StripeService();
  }

  /**
   * Create Payment Intent
   */
  createPaymentIntent = async (
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> => {
    try {
      // Validate request
      const data = PaymentIntentSchema.parse(req.body);

      // Create payment intent
      const result = await this.stripeService.createPaymentIntent(data);

      res.json(result);
    } catch (error) {
      next(error);
    }
  };

  /**
   * Get Payment Intent
   */
  getPaymentIntent = async (
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> => {
    try {
      const { id } = req.params;
      const paymentIntent = await this.stripeService.getPaymentIntent(id);

      res.json(paymentIntent);
    } catch (error) {
      next(error);
    }
  };

  /**
   * Process Refund
   */
  createRefund = async (
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> => {
    try {
      const result = await this.stripeService.createRefund(req.body);
      res.json(result);
    } catch (error) {
      next(error);
    }
  };
}
```

### 4. Webhook Handler

```typescript
// src/controllers/webhook.controller.ts
import { Request, Response } from 'express';
import { StripeService } from '../services/stripe.service';
import Stripe from 'stripe';

export class WebhookController {
  private stripeService: StripeService;

  constructor() {
    this.stripeService = new StripeService();
  }

  /**
   * Handle Stripe Webhooks
   * Context7: Latest webhook handling patterns
   */
  handleStripeWebhook = async (req: Request, res: Response): Promise<void> => {
    const signature = req.headers['stripe-signature'] as string;

    let event: Stripe.Event;

    try {
      // Verify webhook signature (SECURITY!)
      event = this.stripeService.constructWebhookEvent(
        req.body,
        signature
      );
    } catch (error) {
      console.error('Webhook signature verification failed:', error);
      res.status(400).send('Invalid signature');
      return;
    }

    // Handle event types
    try {
      switch (event.type) {
        case 'payment_intent.succeeded':
          await this.handlePaymentIntentSucceeded(
            event.data.object as Stripe.PaymentIntent
          );
          break;

        case 'payment_intent.payment_failed':
          await this.handlePaymentIntentFailed(
            event.data.object as Stripe.PaymentIntent
          );
          break;

        case 'charge.refunded':
          await this.handleChargeRefunded(
            event.data.object as Stripe.Charge
          );
          break;

        case 'customer.subscription.created':
          await this.handleSubscriptionCreated(
            event.data.object as Stripe.Subscription
          );
          break;

        case 'customer.subscription.deleted':
          await this.handleSubscriptionCanceled(
            event.data.object as Stripe.Subscription
          );
          break;

        default:
          console.log(`Unhandled event type: ${event.type}`);
      }

      res.json({ received: true });
    } catch (error) {
      console.error('Webhook processing error:', error);
      res.status(500).send('Webhook processing failed');
    }
  };

  private async handlePaymentIntentSucceeded(
    paymentIntent: Stripe.PaymentIntent
  ): Promise<void> {
    console.log('Payment succeeded:', paymentIntent.id);

    const orderId = paymentIntent.metadata.orderId;
    // Update order status in database
    // await orderService.markAsPaid(orderId);
  }

  private async handlePaymentIntentFailed(
    paymentIntent: Stripe.PaymentIntent
  ): Promise<void> {
    console.log('Payment failed:', paymentIntent.id);

    // Notify user about failed payment
    // await notificationService.sendPaymentFailedEmail(paymentIntent);
  }

  private async handleChargeRefunded(charge: Stripe.Charge): Promise<void> {
    console.log('Charge refunded:', charge.id);

    // Process refund in database
    // await refundService.processRefund(charge);
  }

  private async handleSubscriptionCreated(
    subscription: Stripe.Subscription
  ): Promise<void> {
    console.log('Subscription created:', subscription.id);
  }

  private async handleSubscriptionCanceled(
    subscription: Stripe.Subscription
  ): Promise<void> {
    console.log('Subscription canceled:', subscription.id);
  }
}
```

### 5. Express Routes

```typescript
// src/routes/payment.routes.ts
import { Router } from 'express';
import { PaymentController } from '../controllers/payment.controller';
import { WebhookController } from '../controllers/webhook.controller';
import express from 'express';

const router = Router();
const paymentController = new PaymentController();
const webhookController = new WebhookController();

// Payment routes
router.post('/create-payment-intent', paymentController.createPaymentIntent);
router.get('/payment-intent/:id', paymentController.getPaymentIntent);
router.post('/refund', paymentController.createRefund);

// Webhook route (raw body needed for signature verification)
router.post(
  '/webhook/stripe',
  express.raw({ type: 'application/json' }),
  webhookController.handleStripeWebhook
);

export default router;
```

### 6. Express App Setup

```typescript
// src/app.ts
import express, { Express, Request, Response, NextFunction } from 'express';
import paymentRoutes from './routes/payment.routes';
import { env } from './config/env';

const app: Express = express();

// JSON parsing (except for webhooks - they need raw body)
app.use((req, res, next) => {
  if (req.originalUrl === '/api/payment/webhook/stripe') {
    next();
  } else {
    express.json()(req, res, next);
  }
});

// Routes
app.use('/api/payment', paymentRoutes);

// Error handler
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Error:', err);

  res.status(500).json({
    error: 'internal_error',
    message: err.message,
  });
});

const PORT = env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

export default app;
```

---

## Razorpay Implementation (TypeScript)

```typescript
// src/services/razorpay.service.ts
import Razorpay from 'razorpay';
import crypto from 'crypto';
import { env } from '../config/env';

export interface RazorpayOrderRequest {
  amount: number; // in paise
  currency: string;
  receipt: string;
  orderId: string;
  userId: string;
}

export class RazorpayService {
  private razorpay: Razorpay;

  constructor() {
    // Context7: Check latest Razorpay initialization
    this.razorpay = new Razorpay({
      key_id: env.RAZORPAY_KEY_ID,
      key_secret: env.RAZORPAY_KEY_SECRET,
    });
  }

  /**
   * Create Order
   * Context7: Latest Razorpay order API
   */
  async createOrder(request: RazorpayOrderRequest): Promise<any> {
    try {
      const options = {
        amount: request.amount,
        currency: request.currency,
        receipt: request.receipt,
        notes: {
          orderId: request.orderId,
          userId: request.userId,
        },
      };

      return await this.razorpay.orders.create(options);
    } catch (error) {
      throw new Error(`Razorpay order creation failed: ${error}`);
    }
  }

  /**
   * Verify Payment Signature (CRITICAL!)
   * Context7: Latest signature verification algorithm
   */
  verifyPaymentSignature(
    orderId: string,
    paymentId: string,
    signature: string
  ): boolean {
    try {
      const body = `${orderId}|${paymentId}`;

      const expectedSignature = crypto
        .createHmac('sha256', env.RAZORPAY_KEY_SECRET)
        .update(body)
        .digest('hex');

      return expectedSignature === signature;
    } catch (error) {
      console.error('Signature verification failed:', error);
      return false;
    }
  }

  /**
   * Verify Webhook Signature
   */
  verifyWebhookSignature(payload: string, signature: string): boolean {
    try {
      const expectedSignature = crypto
        .createHmac('sha256', env.RAZORPAY_WEBHOOK_SECRET)
        .update(payload)
        .digest('hex');

      return expectedSignature === signature;
    } catch (error) {
      console.error('Webhook verification failed:', error);
      return false;
    }
  }
}
```

---

## NestJS Implementation (Alternative)

```typescript
// src/payment/payment.module.ts
import { Module } from '@nestjs/common';
import { PaymentService } from './payment.service';
import { PaymentController } from './payment.controller';
import { WebhookController } from './webhook.controller';

@Module({
  controllers: [PaymentController, WebhookController],
  providers: [PaymentService],
  exports: [PaymentService],
})
export class PaymentModule {}
```

```typescript
// src/payment/payment.service.ts
import { Injectable } from '@nestjs/common';
import Stripe from 'stripe';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class PaymentService {
  private stripe: Stripe;

  constructor(private configService: ConfigService) {
    this.stripe = new Stripe(
      this.configService.get<string>('STRIPE_SECRET_KEY')!,
      {
        apiVersion: '2023-10-16',
        typescript: true,
      }
    );
  }

  async createPaymentIntent(data: CreatePaymentIntentDto): Promise<any> {
    // Implementation...
  }
}
```

---

## Testing

```typescript
// src/services/__tests__/stripe.service.test.ts
import { StripeService } from '../stripe.service';
import Stripe from 'stripe';

jest.mock('stripe');

describe('StripeService', () => {
  let stripeService: StripeService;
  let mockStripe: jest.Mocked<Stripe>;

  beforeEach(() => {
    stripeService = new StripeService();
    mockStripe = (Stripe as any).mock.instances[0];
  });

  describe('createPaymentIntent', () => {
    it('should create a payment intent successfully', async () => {
      const mockPaymentIntent = {
        id: 'pi_test_123',
        client_secret: 'pi_test_123_secret',
      };

      mockStripe.paymentIntents.create = jest
        .fn()
        .mockResolvedValue(mockPaymentIntent);

      const request = {
        amount: 1000,
        currency: 'usd',
        orderId: 'order_123',
        userId: 'user_123',
      };

      const result = await stripeService.createPaymentIntent(request);

      expect(result.intentId).toBe('pi_test_123');
      expect(result.clientSecret).toBe('pi_test_123_secret');
    });

    it('should handle card errors', async () => {
      mockStripe.paymentIntents.create = jest
        .fn()
        .mockRejectedValue(
          new Stripe.errors.StripeCardError({
            message: 'Card declined',
            type: 'card_error',
            code: 'card_declined',
          } as any)
        );

      await expect(
        stripeService.createPaymentIntent({} as any)
      ).rejects.toThrow('Card error');
    });
  });
});
```

---

## Context7 Query Examples

**Always query Context7 before implementation:**

```typescript
// Example 1: Latest Stripe API
"Stripe TypeScript SDK 2026 latest PaymentIntent API"

// Example 2: Webhook types
"Stripe TypeScript webhook event types latest"

// Example 3: Error handling
"Stripe TypeScript error handling best practices 2026"

// Example 4: Razorpay
"Razorpay TypeScript Node.js integration latest documentation"

// Example 5: PayPal
"PayPal TypeScript SDK REST API latest 2026"
```

---

## Security Best Practices

✅ API keys in environment variables
✅ Webhook signature verification
✅ Request validation with Zod/Joi
✅ HTTPS only
✅ Rate limiting
✅ Logging payment events
✅ Error handling with proper types
✅ Idempotency keys

---

## When to Use This Skill

✅ TypeScript/Node.js payment integration
✅ Express or NestJS applications
✅ Type-safe payment implementations
✅ Webhook handling
✅ Subscription billing
✅ Refund processing

---

## Status

**Version:** 1.0.0
**Context7 Integration:** MANDATORY
**Language:** TypeScript
**Frameworks:** Express, NestJS
**Security Level:** HIGH
**Production Ready:** ✅

---

**Remember:** ALWAYS query Context7 for latest TypeScript types and APIs!
Payment SDKs evolve rapidly - stay updated! 🚀
