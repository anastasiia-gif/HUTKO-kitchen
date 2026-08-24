# HUTKO — v1.5 (social link previews)

Makes shared links show a proper card (title + photo) instead of a bare grey link on
WhatsApp, Instagram, Facebook, Telegram, iMessage, etc. **Frontend-only. No backend, no
database, data untouched.**

## Why this is separate from the SEO work
The SEO bundle (v1.4) already adds these tags for **Google** via JavaScript. But the apps that
build link-preview cards (WhatsApp/Facebook/Instagram) **don't run JavaScript** — they only
read the raw HTML. So for *those*, the tags have to be written into the page files directly.
That's what this does.

## Files to replace (4)
```
frontend/index.html      frontend/shop.html      frontend/about.html      frontend/contact.html
```
Only the `<head>` changed — a block of Open Graph + Twitter tags was added right after the
`<title>`. The rest of every page is byte-for-byte identical to what's live now (verified).

## The share image
All four use your hero photo: `assets/intro_img.PNG` (the syrnyky / borscht / chicken plate).
It already exists on the site, so nothing else to upload. If you'd ever like a dedicated
1200×630 share image, swap that one file and every preview updates.

## Deploy
Replace the 4 files, commit & push. Roll back anytime by reverting the commit.

## Test after deploy (1 min)
- Fastest: open Facebook's free **Sharing Debugger** (https://developers.facebook.com/tools/debug/),
  paste `https://hutko-kitchen.com/`, click **Scrape Again** → you should see the title + photo.
- Or just paste your link into a WhatsApp chat to yourself — the card should appear.
- (If an app cached the old bare link, use the debugger's "Scrape Again" to refresh it.)

## Not included on purpose
- **product.html** — one product page serves every dish (`product.html?id=…`), so a static card
  can only show a generic HUTKO card, not the specific dish. Real per-dish previews need the
  multilingual/pre-render rebuild (Part C). Product links still show correctly to Google today.
- **delivery.html** — rarely shared to social; easy to add later if you want it.
Both can be added anytime — just say the word.

## Tested before shipping
Automated check on all 4 files: exactly one Open Graph title + Twitter card each, a description
present, the page body unchanged, and valid HTML end. ✅
