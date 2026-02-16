# Payment Integration Expert (Java/Spring Boot)

## Skill Identity
- **Name:** payment-integration-java
- **Version:** 1.0.0
- **Type:** Implementation Specialist
- **Language:** Java (Spring Boot)
- **Domain:** Payment Gateway Integration

---

## Purpose

Expert in integrating payment gateways (Stripe, Razorpay, PayPal, etc.) into Java/Spring Boot applications with secure, production-ready implementations.

---

## Context7 Integration (CRITICAL!)

**ALWAYS use Context7 for latest payment gateway docs!**

### Before Any Implementation:

```java
// Fetch latest docs via Context7
context7.search("Stripe Java SDK latest documentation 2026");
context7.search("Razorpay Java integration Spring Boot latest");
context7.search("PayPal Java SDK v2 latest 2026");
```

**Why Context7:**
- Payment SDKs update frequently
- Security patches released regularly
- New API versions deprecate old ones
- Compliance requirements evolve
- Best practices change

**When to Use:**
1. Before implementing any payment gateway
2. When setting up webhooks
3. For PCI DSS compliance
4. For 3D Secure implementation
5. For subscription billing
6. When errors occur (check latest error codes)

---

## Supported Payment Gateways

### 1. Stripe (Most Popular Globally)
**Use Cases:** SaaS, e-commerce, subscriptions
**Context7 Query:** `"Stripe Java SDK Spring Boot 2026 latest"`

### 2. Razorpay (India Market Leader)
**Use Cases:** Indian payments, UPI, cards, netbanking
**Context7 Query:** `"Razorpay Java SDK latest documentation 2026"`

### 3. PayPal
**Use Cases:** Global payments, buyer protection
**Context7 Query:** `"PayPal Java SDK v2 REST API latest"`

### 4. Square
**Use Cases:** Retail, POS integration
**Context7 Query:** `"Square Java SDK latest 2026"`

### 5. Braintree (PayPal owned)
**Use Cases:** Complex payment flows
**Context7 Query:** `"Braintree Java SDK latest documentation"`

---

## Maven Dependencies

```xml
<!-- pom.xml -->
<dependencies>
    <!-- Spring Boot Starter Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- Stripe Java SDK (Context7: check latest version) -->
    <dependency>
        <groupId>com.stripe</groupId>
        <artifactId>stripe-java</artifactId>
        <version>24.5.0</version>
    </dependency>

    <!-- Razorpay Java SDK -->
    <dependency>
        <groupId>com.razorpay</groupId>
        <artifactId>razorpay-java</artifactId>
        <version>1.4.6</version>
    </dependency>

    <!-- PayPal SDK -->
    <dependency>
        <groupId>com.paypal.sdk</groupId>
        <artifactId>checkout-sdk</artifactId>
        <version>2.0.0</version>
    </dependency>

    <!-- Lombok (optional, for cleaner code) -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
</dependencies>
```

---

## Configuration (application.yml)

```yaml
# application.yml
stripe:
  api-key: ${STRIPE_SECRET_KEY}
  publishable-key: ${STRIPE_PUBLISHABLE_KEY}
  webhook-secret: ${STRIPE_WEBHOOK_SECRET}

razorpay:
  key-id: ${RAZORPAY_KEY_ID}
  key-secret: ${RAZORPAY_KEY_SECRET}

paypal:
  client-id: ${PAYPAL_CLIENT_ID}
  client-secret: ${PAYPAL_CLIENT_SECRET}
  mode: sandbox  # Change to 'live' for production

payment:
  success-url: ${BASE_URL}/payment/success
  cancel-url: ${BASE_URL}/payment/cancel
```

**Configuration Class:**
```java
@Configuration
@ConfigurationProperties(prefix = "stripe")
@Data
public class StripeConfig {
    private String apiKey;
    private String publishableKey;
    private String webhookSecret;

    @PostConstruct
    public void init() {
        Stripe.apiKey = apiKey;
    }
}
```

---

## Stripe Implementation (Spring Boot)

### 1. Payment Intent Creation

```java
@RestController
@RequestMapping("/api/payment/stripe")
@RequiredArgsConstructor
public class StripePaymentController {

    private final StripeConfig stripeConfig;

    /**
     * Create Payment Intent
     * Context7: Check latest PaymentIntent API parameters
     */
    @PostMapping("/create-payment-intent")
    public ResponseEntity<?> createPaymentIntent(@RequestBody PaymentRequest request) {
        try {
            // Context7: Verify latest PaymentIntent.create() parameters
            PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
                .setAmount(request.getAmount()) // in cents
                .setCurrency(request.getCurrency())
                .setAutomaticPaymentMethods(
                    PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
                        .setEnabled(true)
                        .build()
                )
                .putMetadata("orderId", request.getOrderId())
                .putMetadata("userId", request.getUserId())
                .build();

            PaymentIntent intent = PaymentIntent.create(params);

            Map<String, String> response = new HashMap<>();
            response.put("clientSecret", intent.getClientSecret());
            response.put("intentId", intent.getId());

            return ResponseEntity.ok(response);

        } catch (StripeException e) {
            return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * Retrieve Payment Intent
     */
    @GetMapping("/payment-intent/{id}")
    public ResponseEntity<?> getPaymentIntent(@PathVariable String id) {
        try {
            PaymentIntent intent = PaymentIntent.retrieve(id);
            return ResponseEntity.ok(intent);
        } catch (StripeException e) {
            return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body(Map.of("error", e.getMessage()));
        }
    }
}
```

### 2. Webhook Handler (CRITICAL for Security!)

```java
@RestController
@RequestMapping("/api/webhook")
@Slf4j
public class StripeWebhookController {

    @Value("${stripe.webhook-secret}")
    private String webhookSecret;

    /**
     * Handle Stripe Webhooks
     * Context7: Check latest webhook signature verification method
     */
    @PostMapping("/stripe")
    public ResponseEntity<String> handleStripeWebhook(
            @RequestBody String payload,
            @RequestHeader("Stripe-Signature") String sigHeader) {

        Event event;

        try {
            // SECURITY: Verify webhook signature
            // Context7: Latest signature verification best practices
            event = Webhook.constructEvent(payload, sigHeader, webhookSecret);

        } catch (SignatureVerificationException e) {
            log.error("Webhook signature verification failed: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Invalid signature");
        }

        // Handle different event types
        switch (event.getType()) {
            case "payment_intent.succeeded":
                handlePaymentIntentSucceeded(event);
                break;

            case "payment_intent.payment_failed":
                handlePaymentIntentFailed(event);
                break;

            case "charge.refunded":
                handleChargeRefunded(event);
                break;

            case "customer.subscription.created":
                handleSubscriptionCreated(event);
                break;

            case "customer.subscription.deleted":
                handleSubscriptionCanceled(event);
                break;

            default:
                log.info("Unhandled event type: {}", event.getType());
        }

        return ResponseEntity.ok("Success");
    }

    private void handlePaymentIntentSucceeded(Event event) {
        PaymentIntent paymentIntent = (PaymentIntent) event.getData().getObject();
        log.info("Payment succeeded: {}", paymentIntent.getId());

        // Update order status in database
        String orderId = paymentIntent.getMetadata().get("orderId");
        // orderService.markAsPaid(orderId);
    }

    private void handlePaymentIntentFailed(Event event) {
        PaymentIntent paymentIntent = (PaymentIntent) event.getData().getObject();
        log.error("Payment failed: {}", paymentIntent.getId());

        // Notify user about failed payment
        // notificationService.sendPaymentFailedEmail(paymentIntent);
    }

    private void handleChargeRefunded(Event event) {
        Charge charge = (Charge) event.getData().getObject();
        log.info("Charge refunded: {}", charge.getId());

        // Process refund in database
        // refundService.processRefund(charge);
    }
}
```

### 3. Service Layer

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class StripePaymentService {

    private final StripeConfig stripeConfig;

    /**
     * Create Payment Intent with comprehensive error handling
     * Context7: Latest error types and handling strategies
     */
    public PaymentIntentResponse createPaymentIntent(PaymentRequest request) {
        try {
            PaymentIntentCreateParams params = buildPaymentIntentParams(request);
            PaymentIntent intent = PaymentIntent.create(params);

            return PaymentIntentResponse.builder()
                .success(true)
                .clientSecret(intent.getClientSecret())
                .intentId(intent.getId())
                .build();

        } catch (CardException e) {
            // Card was declined
            log.error("Card declined: {}", e.getMessage());
            return PaymentIntentResponse.builder()
                .success(false)
                .error("card_declined")
                .message(e.getMessage())
                .build();

        } catch (RateLimitException e) {
            // Too many requests
            log.error("Rate limit exceeded: {}", e.getMessage());
            return PaymentIntentResponse.builder()
                .success(false)
                .error("rate_limit")
                .message("Too many requests. Please try again later.")
                .build();

        } catch (InvalidRequestException e) {
            // Invalid parameters
            log.error("Invalid request: {}", e.getMessage());
            return PaymentIntentResponse.builder()
                .success(false)
                .error("invalid_request")
                .message(e.getMessage())
                .build();

        } catch (AuthenticationException e) {
            // Authentication failed
            log.error("Authentication failed: {}", e.getMessage());
            return PaymentIntentResponse.builder()
                .success(false)
                .error("authentication_failed")
                .build();

        } catch (APIConnectionException e) {
            // Network error
            log.error("Network error: {}", e.getMessage());
            return PaymentIntentResponse.builder()
                .success(false)
                .error("network_error")
                .build();

        } catch (StripeException e) {
            // Generic Stripe error
            log.error("Stripe error: {}", e.getMessage());
            return PaymentIntentResponse.builder()
                .success(false)
                .error("stripe_error")
                .message(e.getMessage())
                .build();
        }
    }

    /**
     * Process refund
     * Context7: Latest refund API parameters
     */
    public RefundResponse processRefund(String paymentIntentId, Long amount, String reason) {
        try {
            RefundCreateParams params = RefundCreateParams.builder()
                .setPaymentIntent(paymentIntentId)
                .setAmount(amount) // Optional: partial refund
                .setReason(RefundCreateParams.Reason.valueOf(reason.toUpperCase()))
                .build();

            Refund refund = Refund.create(params);

            return RefundResponse.builder()
                .success(true)
                .refundId(refund.getId())
                .status(refund.getStatus())
                .amount(refund.getAmount())
                .build();

        } catch (StripeException e) {
            log.error("Refund failed: {}", e.getMessage());
            return RefundResponse.builder()
                .success(false)
                .error(e.getMessage())
                .build();
        }
    }

    private PaymentIntentCreateParams buildPaymentIntentParams(PaymentRequest request) {
        return PaymentIntentCreateParams.builder()
            .setAmount(request.getAmount())
            .setCurrency(request.getCurrency())
            .setAutomaticPaymentMethods(
                PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
                    .setEnabled(true)
                    .build()
            )
            .putMetadata("orderId", request.getOrderId())
            .putMetadata("userId", request.getUserId())
            .setDescription(request.getDescription())
            .build();
    }
}
```

---

## Razorpay Implementation (India)

### 1. Configuration

```java
@Configuration
@Data
@ConfigurationProperties(prefix = "razorpay")
public class RazorpayConfig {
    private String keyId;
    private String keySecret;

    @Bean
    public RazorpayClient razorpayClient() throws RazorpayException {
        return new RazorpayClient(keyId, keySecret);
    }
}
```

### 2. Order Creation

```java
@RestController
@RequestMapping("/api/payment/razorpay")
@RequiredArgsConstructor
public class RazorpayPaymentController {

    private final RazorpayClient razorpayClient;

    /**
     * Create Razorpay Order
     * Context7: Latest Razorpay order creation API
     */
    @PostMapping("/create-order")
    public ResponseEntity<?> createOrder(@RequestBody RazorpayOrderRequest request) {
        try {
            JSONObject orderRequest = new JSONObject();
            orderRequest.put("amount", request.getAmount()); // in paise
            orderRequest.put("currency", "INR");
            orderRequest.put("receipt", request.getReceiptId());

            // Notes/metadata
            JSONObject notes = new JSONObject();
            notes.put("orderId", request.getOrderId());
            notes.put("userId", request.getUserId());
            orderRequest.put("notes", notes);

            // Context7: Check latest order.create() parameters
            Order order = razorpayClient.orders.create(orderRequest);

            Map<String, Object> response = new HashMap<>();
            response.put("orderId", order.get("id"));
            response.put("amount", order.get("amount"));
            response.put("currency", order.get("currency"));

            return ResponseEntity.ok(response);

        } catch (RazorpayException e) {
            return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", e.getMessage()));
        }
    }

    /**
     * Verify Payment Signature (CRITICAL!)
     * Context7: Latest signature verification algorithm
     */
    @PostMapping("/verify-payment")
    public ResponseEntity<?> verifyPayment(@RequestBody RazorpayPaymentVerification verification) {
        try {
            // Generate signature
            String generatedSignature = generateSignature(
                verification.getRazorpayOrderId(),
                verification.getRazorpayPaymentId()
            );

            // Verify signature
            if (generatedSignature.equals(verification.getRazorpaySignature())) {
                // Signature valid - process payment
                processSuccessfulPayment(verification);
                return ResponseEntity.ok(Map.of("status", "success"));
            } else {
                return ResponseEntity
                    .status(HttpStatus.BAD_REQUEST)
                    .body(Map.of("error", "Invalid signature"));
            }

        } catch (Exception e) {
            return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", e.getMessage()));
        }
    }

    private String generateSignature(String orderId, String paymentId) {
        try {
            String payload = orderId + "|" + paymentId;
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKey = new SecretKeySpec(
                razorpayConfig.getKeySecret().getBytes(StandardCharsets.UTF_8),
                "HmacSHA256"
            );
            mac.init(secretKey);
            byte[] hash = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
            return Hex.encodeHexString(hash);
        } catch (Exception e) {
            throw new RuntimeException("Signature generation failed", e);
        }
    }
}
```

### 3. Razorpay Webhook

```java
@PostMapping("/webhook/razorpay")
public ResponseEntity<String> handleRazorpayWebhook(
        @RequestBody String payload,
        @RequestHeader("X-Razorpay-Signature") String signature) {

    try {
        // Verify webhook signature
        // Context7: Latest Razorpay webhook verification
        if (!verifyRazorpayWebhookSignature(payload, signature)) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Invalid signature");
        }

        JSONObject event = new JSONObject(payload);
        String eventType = event.getString("event");

        switch (eventType) {
            case "payment.captured":
                handlePaymentCaptured(event);
                break;

            case "payment.failed":
                handlePaymentFailed(event);
                break;

            case "refund.processed":
                handleRefundProcessed(event);
                break;

            default:
                log.info("Unhandled event type: {}", eventType);
        }

        return ResponseEntity.ok("Success");

    } catch (Exception e) {
        log.error("Webhook processing failed: {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error");
    }
}
```

---

## DTOs (Data Transfer Objects)

```java
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class PaymentRequest {
    private Long amount;
    private String currency;
    private String orderId;
    private String userId;
    private String description;
}

@Data
@Builder
public class PaymentIntentResponse {
    private boolean success;
    private String clientSecret;
    private String intentId;
    private String error;
    private String message;
}

@Data
@Builder
public class RefundResponse {
    private boolean success;
    private String refundId;
    private String status;
    private Long amount;
    private String error;
}

@Data
public class RazorpayPaymentVerification {
    private String razorpayOrderId;
    private String razorpayPaymentId;
    private String razorpaySignature;
}
```

---

## Exception Handling

```java
@RestControllerAdvice
public class PaymentExceptionHandler {

    @ExceptionHandler(StripeException.class)
    public ResponseEntity<?> handleStripeException(StripeException e) {
        log.error("Stripe error: {}", e.getMessage());

        Map<String, String> error = new HashMap<>();
        error.put("error", "payment_error");
        error.put("message", e.getMessage());

        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    @ExceptionHandler(RazorpayException.class)
    public ResponseEntity<?> handleRazorpayException(RazorpayException e) {
        log.error("Razorpay error: {}", e.getMessage());

        Map<String, String> error = new HashMap<>();
        error.put("error", "payment_error");
        error.put("message", e.getMessage());

        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }
}
```

---

## Testing

```java
@SpringBootTest
@AutoConfigureMockMvc
class StripePaymentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private StripePaymentService paymentService;

    @Test
    void testCreatePaymentIntent() throws Exception {
        // Arrange
        PaymentRequest request = PaymentRequest.builder()
            .amount(1000L)
            .currency("usd")
            .orderId("order_123")
            .build();

        PaymentIntentResponse response = PaymentIntentResponse.builder()
            .success(true)
            .clientSecret("pi_secret_123")
            .intentId("pi_123")
            .build();

        when(paymentService.createPaymentIntent(any())).thenReturn(response);

        // Act & Assert
        mockMvc.perform(post("/api/payment/stripe/create-payment-intent")
                .contentType(MediaType.APPLICATION_JSON)
                .content(new ObjectMapper().writeValueAsString(request)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.success").value(true))
            .andExpect(jsonPath("$.clientSecret").exists());
    }
}
```

---

## Context7 Query Examples

**Before implementing features, always query Context7:**

```java
// Example 1: Payment Intent
"Stripe Java SDK PaymentIntent latest API 2026"

// Example 2: Webhooks
"Stripe webhook signature verification Java Spring Boot best practices"

// Example 3: 3D Secure
"Stripe 3D Secure 2 Java implementation latest"

// Example 4: Razorpay Orders
"Razorpay Java SDK order creation latest documentation"

// Example 5: PayPal Integration
"PayPal Java SDK v2 Spring Boot integration 2026"
```

---

## Security Checklist

✅ API keys in environment variables (never hardcoded)
✅ Webhook signature verification (ALWAYS!)
✅ HTTPS only in production
✅ Idempotency keys for retries
✅ Amount validation server-side
✅ Rate limiting on payment endpoints
✅ Logging all payment events
✅ PCI DSS compliance (use hosted checkout)

---

## When to Use This Skill

✅ Payment gateway integration in Java/Spring Boot
✅ E-commerce checkout implementation
✅ Subscription billing
✅ Webhook setup
✅ Refund processing
✅ Payment status tracking

---

## Status

**Version:** 1.0.0
**Context7 Integration:** MANDATORY
**Framework:** Spring Boot 3.x
**Security Level:** HIGH
**Production Ready:** ✅

---

**Remember:** ALWAYS query Context7 before implementing payment features!
Payment SDKs update frequently - stay current! 🚀
