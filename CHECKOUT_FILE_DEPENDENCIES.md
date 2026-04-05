# 📁 Files Needed to Modify checkout.html

## Core Files (Required)

### 1. **Main Template File**
- `Files/templates/checkout.html` - The main checkout page template

### 2. **Backend Route (Flask)**
- `Files/main.py` - Contains routes that serve checkout.html:
  - `/checkout` route (line 12-14)
  - `/checkOut` route (line 16-18)
  - Other routes that redirect to checkout

---

## JavaScript Dependencies (Imported Modules)

### 3. **Firebase Integration**
- `Files/static/js/firebase-integration.js` - **CRITICAL**
  - Cart persistence (saveCartToFirebase, loadCartFromFirebase)
  - User authentication state
  - Firestore operations
  - Used via: `import * as FirebaseModule from '/static/js/firebase-integration.js'`

### 4. **Payment Modal**
- `Files/static/js/payment-modal.js` - **CRITICAL**
  - Payment modal creation and management
  - Used via: `import { createPaymentModal, initPaymentModal, openPaymentModal } from '/static/js/payment-modal.js'`

### 5. **Auth Modal**
- `Files/static/js/auth-modal-professional.js` - **CRITICAL**
  - Login/register modal
  - Used via: `import { createAuthModal } from '/static/js/auth-modal-professional.js'`

---

## CSS Files (Stylesheets)

### 6. **Bootstrap CSS**
- `Files/static/css/bootstrap.css` - Bootstrap framework styles

### 7. **Main Stylesheet**
- `Files/static/css/style.css` - Main application styles

### 8. **Fast Hover Effects**
- `Files/static/css/fasthover.css` - Hover animations

### 9. **Modern Design**
- `Files/static/css/modern-design.css` - Modern design system styles

### 10. **Inline CSS (in checkout.html)**
- Lines 16-1146 in `checkout.html` - All custom checkout styles are inline
- **Note:** Most checkout-specific CSS is embedded in the HTML file itself

---

## JavaScript Libraries (External/CDN)

### 11. **jQuery**
- `Files/static/js/jquery.min.js` - jQuery library (loaded before checkout scripts)

### 12. **Bootstrap JS**
- `Files/static/js/bootstrap-3.1.1.min.js` - Bootstrap JavaScript

---

## Related Files (May Need Updates)

### 13. **Product Page**
- `Files/templates/product.html` - **IMPORTANT**
  - Adds items to cart
  - Cart format must match checkout expectations
  - Price extraction logic should match checkout

### 14. **Home/Index Page**
- `Files/templates/index.html` - May link to checkout

### 15. **Cart Logic (Shared)**
- Cart structure is shared between:
  - `product.html` (adds items)
  - `checkout.html` (displays items)
  - Both use same `localStorage` key: `'cart'`
  - Both use same Firebase collection: `'carts'`

---

## File Structure Summary

```
Virtual-Trial-Room/
├── Files/
│   ├── main.py                          ← Backend routes
│   ├── templates/
│   │   ├── checkout.html                ← MAIN FILE
│   │   ├── product.html                 ← Adds to cart
│   │   └── index.html                  ← Home page
│   └── static/
│       ├── css/
│       │   ├── bootstrap.css            ← Bootstrap styles
│       │   ├── style.css                ← Main styles
│       │   ├── fasthover.css            ← Hover effects
│       │   └── modern-design.css        ← Modern design
│       └── js/
│           ├── firebase-integration.js  ← Firebase & cart
│           ├── payment-modal.js         ← Payment UI
│           ├── auth-modal-professional.js ← Login modal
│           ├── jquery.min.js            ← jQuery
│           └── bootstrap-3.1.1.min.js  ← Bootstrap JS
```

---

## What Each File Does

### checkout.html
- **Purpose:** Main checkout page template
- **Contains:**
  - HTML structure
  - Inline CSS (lines 16-1146)
  - JavaScript cart logic (lines 1148+)
  - Product price mapping
  - Cart display functions

### firebase-integration.js
- **Purpose:** Firebase/Firestore operations
- **Functions used:**
  - `saveCartToFirebase(cart)` - Save cart to Firestore
  - `loadCartFromFirebase()` - Load cart from Firestore
  - `isUserLoggedIn()` - Check auth state
  - `onAuthStateChanged()` - Auth state listener

### payment-modal.js
- **Purpose:** Payment modal UI
- **Functions used:**
  - `createPaymentModal()` - Create modal HTML
  - `initPaymentModal(FirebaseModule)` - Initialize with Firebase
  - `openPaymentModal(amount)` - Open modal with price

### auth-modal-professional.js
- **Purpose:** Login/register modal
- **Functions used:**
  - `createAuthModal()` - Create modal HTML
  - `window.openAuthModal()` - Open modal (global)

### product.html
- **Purpose:** Product listing page
- **Important:** Must match cart format used in checkout
- **Shared:**
  - Cart structure: `{ product: string, quantity: number, price: number }`
  - `PRODUCT_PRICES` mapping
  - `addToCart()` function logic

---

## Common Modification Scenarios

### To Change Checkout Layout/Design:
1. ✅ `Files/templates/checkout.html` (CSS section, lines 16-1146)
2. ✅ `Files/static/css/modern-design.css` (if using shared styles)

### To Change Cart Logic:
1. ✅ `Files/templates/checkout.html` (JavaScript section, lines 1148+)
2. ✅ `Files/static/js/firebase-integration.js` (if changing Firebase operations)
3. ✅ `Files/templates/product.html` (must match cart format)

### To Change Price Display:
1. ✅ `Files/templates/checkout.html` (price mapping & display logic)
2. ✅ `Files/templates/product.html` (price extraction when adding to cart)

### To Change Payment Flow:
1. ✅ `Files/templates/checkout.html` (payment button handler)
2. ✅ `Files/static/js/payment-modal.js` (payment modal UI)

### To Change Authentication:
1. ✅ `Files/static/js/firebase-integration.js` (auth logic)
2. ✅ `Files/static/js/auth-modal-professional.js` (login UI)
3. ✅ `Files/templates/checkout.html` (auth UI display)

---

## Quick Reference: Import Statements

```javascript
// In checkout.html (lines 1150-1152, 1189-1190)
import * as FirebaseModule from '/static/js/firebase-integration.js';
import { createPaymentModal, initPaymentModal, openPaymentModal } from '/static/js/payment-modal.js';
import { createAuthModal } from '/static/js/auth-modal-professional.js';
```

---

## Testing Checklist

After modifying checkout.html, test:
- [ ] Cart loads from localStorage
- [ ] Cart loads from Firebase (if logged in)
- [ ] Prices display correctly
- [ ] Quantity adjustments work
- [ ] Remove item works
- [ ] Payment modal opens with correct price
- [ ] Auth modal opens when clicking login
- [ ] Layout is responsive
- [ ] No JavaScript errors in console

---

## Notes

1. **Most CSS is inline** - Checkout styles are in `<style>` tag in checkout.html
2. **Cart format is shared** - product.html and checkout.html must use same structure
3. **Firebase is critical** - Cart persistence depends on firebase-integration.js
4. **Module imports** - Uses ES6 modules, so files must export correctly
5. **Price mapping** - PRODUCT_PRICES object is in both product.html and checkout.html

---

**Total Files to Consider: 15 files**
- **1 Core:** checkout.html
- **3 Critical JS:** firebase-integration.js, payment-modal.js, auth-modal-professional.js
- **4 CSS:** bootstrap.css, style.css, fasthover.css, modern-design.css
- **2 JS Libs:** jquery.min.js, bootstrap-3.1.1.min.js
- **1 Backend:** main.py
- **4 Related:** product.html, index.html, and shared cart logic


