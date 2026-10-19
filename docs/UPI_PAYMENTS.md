# Simple group payments

- **iPhone/iPad (including iPad desktop mode):** Show iOS instructions and the receiver's UPI ID. Pay manually in the payment app, return, and mark paid. Never offer an iOS deep link.
- **Other devices:** Offer a GPay-targeted Android UPI intent for a valid receiver UPI ID. The chosen full/partial amount and suggested payee name are encoded. Android GPay is required; desktop/non-supporting browsers can use the displayed ID manually. No installed-app detection or guaranteed native/P2P acceptance is claimed.
- There is no hosted checkout, provider API, QR generation, PhonePe/CRED option, SDK or extra dependency.

After a successful payment, when the payer explicitly selects **I’ve paid — update balances**, the payment is automatically approved in the app and counted once. This is a user assertion, not bank verification. Opening a native app, cancelling or returning never submits or approves a payment. The receiver can confirm receipt, correct the received amount, or reject it later. Correct/reject recalculates balances and suggestions live. New bills and settlements stay available.

Names do not identify destinations: the receiver's UPI ID selects the account; website/bank names may differ. Users should verify the actual name and UPI ID shown in GPay. Historic destination snapshots stay intact when a profile changes. Signed claim tokens bind users/group/reference/max amount; duplicate claims and confirmations do not double count payments.

Existing pending paid claims are migrated to app auto-approved status once, preserving their amount and history. Bill-share expenses are not recreated for settlements.

## Configuration and checks

No new environment variables or dependencies. Apply migrations:

```sh
.venv/bin/python src/manage.py migrate
.venv/bin/python src/manage.py test apps.groups apps.accounts
node --test tests/settlement.test.cjs
node --check src/apps/groups/static/groups/settlement.js
.venv/bin/python src/manage.py check
.venv/bin/python src/manage.py makemigrations --check --dry-run
```

## Physical-device checklist

1. iPhone Safari/Chrome/PWA and iPad desktop mode: instructions + receiver ID visible; GPay link absent.
2. Android Chrome: valid receiver ID; full/partial amount prefilled in GPay if accepted; verify actual bank recipient before proceeding.
3. Cancel or return without marking paid: no record or balance change. If GPay is missing, the browser fallback returns to the group; manual ID remains available.
4. Explicitly mark a test payment paid: app auto-approved; both users see updated balances without receiver acceptance or page reload.
5. Receiver corrects/rejects: balances recalculate. Retry submission/confirmation: payment counted once.
6. ₹12,000 equal bill → ₹6,000 paid → payer adds a ₹400 equal bill: reverse settlement is ₹200 immediately, without waiting for receipt confirmation.

Browser tests cannot establish native app/bank acceptance or actual money transfer. Source formats: [Google UPI URI/package documentation](https://developers.google.com/pay/india/api/android/in-app-payments), [Android browser intent format](https://developer.chrome.com/docs/android/intents). Google's web integration documentation targets merchant Android Chrome payments; this app does not pretend a personal account is a merchant or fabricate merchant identifiers.

The paid button is the only confirmation action; there is no additional checkbox. The hidden completion marker is submitted only with the explicit form POST.

The keep-awake workflow uses a YAML literal multiline block to preserve shell continuations (the old folded scalar produced malformed curl URLs). It requests `/healthz/` with bounded curl attempts and an 8-minute job timeout, so cold-start retries can finish inside the job budget. This workflow checks service availability; it is not a Django regression-test CI job.
