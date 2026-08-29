# HUTKO — v1.8 (checkout fix + sales tracking)

Two things in one bundle. **Frontend-only, no data touched.**

## 1) Checkout now works WITHOUT Google  (this is the "Pay & Order does nothing" fix)
The top address box was the **Google autocomplete, which is down** (billing). Typing there
saved nothing, so the address counted as empty — but those fields were hidden, so you got
"Please fill in all required fields" while everything visible looked filled.

Fixed:
- The broken Google box is **hidden**.
- The visible address box (street / postcode / city / area) is now **the** address input and
  actually fills the order.
- Clear, correct error messages that point at the real fields (name/email/phone, or the
  address), and highlight them — no more mystery "fill required fields".

## 2) Sales-funnel tracking (GA4)
Events added so you can see the funnel and real orders in GA4:
- `add_to_cart` (in main.js), `begin_checkout` + `purchase` (in checkout).
You'll see these under GA4 → Reports → Engagement → Events, and can mark `purchase` as a key event.

## Files to replace (2)
```
frontend/checkout.html      ← address fix + begin_checkout/purchase events
frontend/js/main.js         ← add_to_cart event  (this main.js also has your GA4 tag + the
                              share-image default — it's the latest, use this one)
```
Replace both, commit & push.

## ⚠️ IMPORTANT — the payment step (please check with the owner)
After this fix, checkout accepts the order and tries to send the customer to **payment (Stripe)**.
For the card payment to actually work, the server needs **`STRIPE_SECRET_KEY`** set on Render
(Render → your service → Environment). If it's missing, orders get *created* but customers can't
pay — and you won't be notified — which may be why completed orders weren't coming through.

Please check Render → Environment for `STRIPE_SECRET_KEY` (and `STRIPE_WEBHOOK_SECRET`). If it's
not there, that's the next thing to fix. Tell me what you find and I'll help — including, if you
want, a change so you're emailed about every order the moment it's placed (even before payment),
so nothing is ever lost.

## Also still pending (separate)
Upload `og-cover.jpg` to `frontend/assets/` for the share card (from the earlier bundle).

## Tested before shipping
Reproduced your exact "fill required fields even when filled" bug in a real browser (with Google
autocomplete forced off, like your live site), then verified: order submits when the address is
filled; clear, correct messages when it isn't; and the funnel events fire. main.js syntax validated.
