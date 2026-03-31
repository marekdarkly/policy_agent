# ToggleBank Open Banking Guide

**Document Reference:** TB-GUIDE-OPEN-BANKING-2026  
**Effective Date:** 1 January 2026  
**Classification:** Customer-Facing

---

## Overview

Open Banking lets you securely share your financial data with authorised third-party providers and initiate payments through apps and services beyond your bank's own channels. It gives you more control over your money and access to a wider range of financial tools.

## What Is Open Banking?

Open Banking was introduced under the **Payment Services Directive 2 (PSD2)**, a European regulation adopted into UK law. It requires banks to allow regulated third-party providers to access customer account data (with your explicit consent) through secure APIs.

Key principles:

- **You are in control** — nothing is shared without your explicit consent.
- **Security** — all connections use bank-grade encryption and authentication.
- **Regulated** — all third-party providers must be authorised by the **Financial Conduct Authority (FCA)** or equivalent European regulator.
- **Revocable** — you can revoke access at any time.

## How It Works

1. **Choose a third-party app or service** — for example, a budgeting tool or payment initiation service.
2. **Grant consent** — the app redirects you to ToggleBank's secure login, where you authenticate with your normal credentials (including two-factor authentication).
3. **Data is shared securely** — the third-party provider receives only the data you consented to share (e.g. transaction history, balances).
4. **Ongoing access** — consent is typically valid for **90 days**, after which you must re-authenticate.

ToggleBank **never shares your login credentials** with third parties. The connection uses secure tokens.

## Types of Third-Party Providers

| Provider Type | What They Do | Example |
|---|---|---|
| **Account Information Service Provider (AISP)** | Views your account data (balances, transactions) | Budgeting apps, credit score services |
| **Payment Initiation Service Provider (PISP)** | Initiates payments from your account on your behalf | Bill payment services, e-commerce checkouts |
| **Card-Based Payment Instrument Issuer (CBPII)** | Checks if sufficient funds are available for a card payment | Prepaid card providers |

## Compatible Apps & Services

ToggleBank's Open Banking APIs are compatible with a wide range of FCA-authorised providers, including:

| App | Type | Description |
|---|---|---|
| **Emma** | AISP | Subscription tracking and budgeting |
| **Plum** | AISP | AI-powered savings and investment |
| **Money Dashboard** | AISP | Multi-bank financial overview |
| **Snoop** | AISP | Bill comparison and savings recommendations |
| **Revolut** | AISP/PISP | Multi-currency accounts and payments |
| **HMRC** | PISP | Direct tax payments from your bank account |
| **Truelayer** | PISP | Payment infrastructure for e-commerce |

## Variable Recurring Payments (VRP)

VRP is a new Open Banking feature that allows authorised third parties to make **recurring payments** from your account, within limits that you control.

- **Sweeping VRP** — Automatically move money between your own accounts (e.g. from your current account to your savings when your balance exceeds a threshold).
- **Commercial VRP** — Pay for subscriptions, memberships, or regular services through a third-party provider (subject to your consent and spending limits).

VRP benefits over Direct Debits:

- **Real-time control** — adjust limits or revoke access instantly in the ToggleBank app.
- **Smarter payments** — payments can be triggered by rules (e.g. "if balance > £2,000, sweep £500 to savings").
- **Instant confirmation** — payment confirmation is immediate (no multi-day clearing cycle).

## Managing Your Connections

You can view and manage all Open Banking connections in the ToggleBank Mobile App or Online Banking:

- **View active connections** — See which providers have access and what data they can see.
- **Revoke access** — Remove a connection at any time. The provider will immediately lose access.
- **Connection history** — View a log of when each provider last accessed your data.

Navigate to: **Settings > Open Banking & Connected Apps**.

## Security & Your Rights

- All providers must be **FCA-authorised** — you can check a provider's status on the FCA Register ([register.fca.org.uk](https://register.fca.org.uk)).
- Your data is protected under **UK GDPR** and the **Data Protection Act 2018**.
- If an unauthorised transaction is made by a PISP, ToggleBank is required to refund you immediately and pursue the matter with the provider.
- You are **never liable** for losses caused by a regulated third-party provider acting outside your consent.

## Frequently Asked Questions

**Is Open Banking safe?**  
Yes. It is regulated by the FCA and uses the same level of security as your Online Banking. Your login credentials are never shared with third parties.

**Will it affect my credit score?**  
Connecting a budgeting app via Open Banking does **not** create a credit search or affect your credit score. However, if you use an app that offers credit products, a separate credit search may apply.

**Can I use Open Banking with joint accounts?**  
Yes. Either account holder can grant Open Banking access. The consent applies to the shared account data.

## Support

- **Open Banking queries:** 0345 678 9012
- **Open Banking Implementation Entity (OBIE):** [openbanking.org.uk](https://openbanking.org.uk)

---

*ToggleBank is authorised by the Prudential Regulation Authority and regulated by the Financial Conduct Authority and the Prudential Regulation Authority (FRN 456789).*
