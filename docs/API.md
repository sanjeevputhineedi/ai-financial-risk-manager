# API Contract Documentation — AI Financial Risk Manager Backend

Backend API Version: `v1`  
Base URL: `/api/v1`  
Protocol: HTTP / JSON  
Authentication: HTTP Bearer Token (`JWT`)

---

## 1. Authentication Endpoints

### `POST /api/v1/auth/register`
Creates a simulated user and initializes a simulated UPI account with an opening balance.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "password": "password123",
  "initial_balance": 25000.0,
  "upi_id": "johndoe@upi"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "username": "johndoe",
  "email": "user@example.com",
  "role": "USER"
}
```

### `POST /api/v1/auth/login`
Authenticates user credentials and issues a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

---

## 2. Users & Accounts Endpoints

### `GET /api/v1/users/me`
Header: `Authorization: Bearer <token>`  
Returns profile details for the authenticated user.

### `GET /api/v1/accounts/me`
Header: `Authorization: Bearer <token>`  
Returns the simulated account details, UPI ID, and current balance.

### `GET /api/v1/recipients`
Header: `Authorization: Bearer <token>`  
Returns list of saved payees/recipients for the user.

### `POST /api/v1/recipients`
Header: `Authorization: Bearer <token>`  
Saves a new recipient with simulated verification status.

---

## 3. Transaction Endpoints

### `POST /api/v1/transactions`
Header: `Authorization: Bearer <token>`  
Initiates a payment transaction, evaluates personal & payee risk, and performs decision routing.

**Request Body:**
```json
{
  "recipient_vpa": "merchant@upi",
  "recipient_name": "Merchant Name",
  "amount": 500.0,
  "notes": "Payment for goods",
  "idempotency_key": "unique-uuid-key",
  "bypass_risk_warning": false
}
```

**Response (201 Created):**
```json
{
  "id": "tx-uuid-1234",
  "idempotency_key": "unique-uuid-key",
  "sender_account_id": "acc-uuid-1234",
  "recipient_vpa": "merchant@upi",
  "recipient_name": "Merchant Name",
  "amount": 500.0,
  "status": "COMPLETED",
  "personal_risk_score": 10.0,
  "payee_risk_score": 5.0,
  "overall_risk_score": 6.8,
  "risk_level": "LOW",
  "decision": "ALLOW",
  "notes": "Payment for goods",
  "created_at": "2026-08-30T10:00:00Z",
  "updated_at": "2026-08-30T10:00:00Z"
}
```

### `POST /api/v1/transactions/{id}/confirm`
Confirms a payment that was placed into `CONFIRMATION_REQUIRED` state.

### `POST /api/v1/transactions/{id}/cancel`
Cancels a payment before funds are finalized.

---

## 4. ML Risk Integration Contract (M5)

### `POST /api/v1/risk/analyze`
Direct interface connecting frontend and decision engine with the AI risk models (Reddy's Payee Risk model + Personal Risk engine).

**Request Body:**
```json
{
  "sender_id": "alice@upi",
  "recipient_id": "suspicious_payee@upi",
  "amount": 8000.0,
  "timestamp": "2026-08-30T10:00:00Z",
  "context": {}
}
```

**Response (200 OK):**
```json
{
  "personal_risk": 55.0,
  "payee_risk": 90.0,
  "overall_risk": 77.8,
  "risk_level": "HIGH",
  "decision": "HOLD",
  "requires_confirmation": true,
  "requires_hold": true,
  "reasons": [
    "Recipient has 8 active fraud report(s) on record.",
    "High transaction velocity in recipient payment network."
  ],
  "model_version": "payee-v1+personal-v1"
}
```

---

## 5. Payees & Fraud Reports

### `GET /api/v1/payees/{id}/risk`
Returns risk score and reasons for a given recipient VPA.

### `GET /api/v1/payees/{id}/reputation`
Returns transaction history stats, complaint count, and reputation score.

### `POST /api/v1/reports`
Header: `Authorization: Bearer <token>`  
Files a fraud/dispute report against a recipient.

**Categories:**
- `SUSPECTED_FRAUD`
- `DELIVERY_DELAY`
- `SERVICE_DISPUTE`
- `REFUND_DISPUTE`
- `OTHER`

---

## 6. Fund Manager & Escrow Cooling Period

### `GET /api/v1/held-payments`
Lists currently held escrow payments.

### `POST /api/v1/held-payments/{id}/release`
Header: `Authorization: Bearer <admin-token>`  
Releases escrow funds from Fund Manager pool to recipient.

### `POST /api/v1/held-payments/{id}/refund`
Header: `Authorization: Bearer <admin-token>`  
Refunds escrow funds from Fund Manager pool back to sender.

### `POST /api/v1/held-payments/reevaluate`
Triggers dynamic cooling re-evaluation across all active held payments.

---

## 7. Audit & Dashboard

### `GET /api/v1/audit`
Header: `Authorization: Bearer <admin-token>`  
Lists immutable, sanitized security audit logs.

### `GET /api/v1/dashboard/metrics`
Aggregates live platform transaction volumes, risk distributions, held funds, and mitigation metrics.
