# CloudKirana Frontend (React + Vite)

Converted from the original static `CloudKirana_App_frontend.html` prototype.
Same screens, same look, same simulated behavior — now as real React components
instead of one HTML file with hidden `<div>`s.

## Run it

```bash
npm install
npm run dev
```

Then open the URL Vite prints (usually http://localhost:5173).

## Build for deployment

```bash
npm run build
```

Output goes to `dist/` — deployable as-is to Vercel, Netlify, etc.

## Structure

```
src/
  App.jsx                    # navigation state + device frame (phone/desktop)
  components/
    RoleSelector.jsx         # 0. role picker
    AuthPhone.jsx            # 1. phone number entry
    AuthOtp.jsx               #    OTP verification
    RetailerDashboard.jsx    # 2. retailer home (stock, ONDC toggle, scan FAB)
    ScannerModal.jsx         #    compliance scan result modal
    InvoiceScanner.jsx       # 3. invoice → inventory digitization
    ConsumerStorefront.jsx   # 4. consumer storefront
    Cart.jsx                 # 5. cart & checkout
    OrderTracking.jsx        # 6. order tracking timeline
    AuthorityDashboard.jsx   # 7. authority control room
    WholesalerPlaceholder.jsx# 8. wholesaler placeholder
```

## What's still simulated (not wired to a backend yet)

- Login accepts any input; OTP is hardcoded to 4092.
- The compliance scan result, invoice line items, inventory numbers, and the
  authority's flagged incident are all hardcoded sample data.
- The invoice scan "Extracting data..." delay is a fixed 1.5s timeout, not a
  real OCR call.

These are exactly the pieces the backend prompt (already written separately)
is meant to replace with real API calls.

## Notes on the conversion

- Font Awesome is loaded via CDN in `index.html`, same as the original.
- Tailwind is now compiled properly through PostCSS instead of the CDN
  `<script>` tag — same utility classes, production-ready output.
- The `.fade-in` animation and `.hide-scrollbar` utility from the original
  `<style>` block now live in `src/index.css`.
- Navigation (`navigateTo`, `startLoginFlow`, `finishLogin`) is now React
  state in `App.jsx` instead of DOM `classList` manipulation.
