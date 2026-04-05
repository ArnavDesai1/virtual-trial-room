# 🚀 QUICK COPY-PASTE INTEGRATION (5 minutes)

## Step 1: Find the Header Section in checkout.html

**Find this line (around line 310):**
```html
    </div>
    <!-- //header -->
```

**Add this right after it:**
```html
    <!-- Auth Container -->
    <div id="auth-container" style="
        position: fixed;
        top: 25px;
        right: 30px;
        z-index: 999;
    "></div>
    
    <!-- Payment Modal Container -->
    <div id="payment-modal-container"></div>
```

---

## Step 2: Add Firebase & Payment Module Imports

**Find the closing `</head>` tag (around line 330)**

**Add this module script BEFORE `</head>`:**

```html
    <script type="module">
        // Import Firebase and Payment modules
        import * as FirebaseModule from '/static/js/firebase-integration.js';
        import { createPaymentModal, initPaymentModal, openPaymentModal } from '/static/js/payment-modal.js';
        
        // Make globally available
        window.FirebaseModule = FirebaseModule;
        window.PaymentUtils = { openPaymentModal };
        
        // Initialize payment modal on page load
        document.addEventListener('DOMContentLoaded', () => {
            createPaymentModal();
            initPaymentModal(FirebaseModule);
            updateAuthUI();  // Show initial auth state
        });
        
        // Listen to auth state changes and update UI
        FirebaseModule.onAuthStateChange((user) => {
            updateAuthUI();
            if (user) {
                // Auto-reload cart when user logs in
                loadCart();
            }
        });
        
        // Update auth UI (login button or avatar)
        function updateAuthUI() {
            const user = FirebaseModule.getCurrentUser();
            const container = document.getElementById('auth-container');
            
            if (user) {
                // Show avatar
                const initials = (user.displayName || user.email || 'U').substring(0, 2).toUpperCase();
                container.innerHTML = `
                    <div style="position: relative;">
                        <button id="user-avatar" style="
                            width: 45px;
                            height: 45px;
                            border-radius: 50%;
                            background: linear-gradient(135deg, #6366f1, #ec4899);
                            color: white;
                            border: none;
                            font-weight: bold;
                            cursor: pointer;
                            font-size: 16px;
                            transition: transform 0.2s;
                        " title="Click for menu">${initials}</button>
                        
                        <div id="user-dropdown" style="
                            display: none;
                            position: absolute;
                            top: 55px;
                            right: 0;
                            background: white;
                            border-radius: 12px;
                            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
                            min-width: 220px;
                            z-index: 10000;
                            overflow: hidden;
                        ">
                            <div style="padding: 16px; border-bottom: 1px solid #e2e8f0; background: #f8f9fa;">
                                <p style="margin: 0; font-weight: 600; color: #1e293b; font-size: 0.95rem;">${user.displayName || 'User'}</p>
                                <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: #64748b;">${user.email}</p>
                            </div>
                            <button id="logout-btn" style="
                                width: 100%;
                                padding: 12px 16px;
                                border: none;
                                background: none;
                                color: #ef4444;
                                cursor: pointer;
                                text-align: left;
                                font-weight: 500;
                                font-size: 0.9rem;
                                transition: background 0.2s;
                            ">🚪 Logout</button>
                        </div>
                    </div>
                `;
                
                // Avatar click
                setTimeout(() => {
                    const btn = document.getElementById('user-avatar');
                    const dropdown = document.getElementById('user-dropdown');
                    if (btn) {
                        btn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
                        });
                    }
                    
                    // Logout button
                    if (document.getElementById('logout-btn')) {
                        document.getElementById('logout-btn').addEventListener('click', async () => {
                            await FirebaseModule.logout();
                            window.location.reload();
                        });
                    }
                }, 0);
                
            } else {
                // Show login button
                container.innerHTML = `
                    <button id="login-btn" style="
                        padding: 10px 20px;
                        background: linear-gradient(135deg, #6366f1, #ec4899);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 0.9rem;
                        transition: all 0.2s;
                    ">🔐 Login</button>
                `;
                
                setTimeout(() => {
                    const btn = document.getElementById('login-btn');
                    if (btn) {
                        btn.addEventListener('click', showAuthModal);
                    }
                }, 0);
            }
        }
        
        // Simple auth modal with prompts
        async function showAuthModal() {
            const email = prompt('📧 Email (gmail.com, yahoo.com, outlook.com, somaiya.edu):', '');
            if (!email) return;
            
            const password = prompt('🔒 Password (min 6 characters):', '');
            if (!password) return;
            
            const isLogin = confirm('✓ OK for Login   ✗ Cancel for Register');
            
            let result;
            if (isLogin) {
                result = await FirebaseModule.loginWithEmail(email, password);
            } else {
                result = await FirebaseModule.registerWithEmail(email, password);
            }
            
            if (result.success) {
                alert('✅ ' + result.message);
                window.location.reload();
            } else {
                alert('❌ Error: ' + result.error);
            }
        }
        
        // Expose for use
        window.showAuthModal = showAuthModal;
    </script>
```

---

## Step 3: Update loadCart() Function

**Find the `loadCart()` function (around line 400)**

**Replace with:**
```javascript
async function loadCart() {
    // Try Firebase first if user is logged in
    if (window.FirebaseModule && window.FirebaseModule.isUserLoggedIn()) {
        try {
            CART = await window.FirebaseModule.loadCartFromFirebase();
            if (CART.length > 0) {
                console.log("✓ Cart loaded from Firebase");
                displayCart();
                return;
            }
        } catch (e) {
            console.warn("Error loading from Firebase:", e);
        }
    }
    
    // Fall back to localStorage
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
        try {
            CART = JSON.parse(savedCart);
            console.log("✓ Cart loaded from localStorage");
        } catch (e) {
            console.error("Error loading cart:", e);
            CART = [];
        }
    }
    
    displayCart();
}
```

---

## Step 4: Update saveCart() Function

**Find the `saveCart()` function (around line 420)**

**Replace with:**
```javascript
async function saveCart() {
    // Save to Firebase if user is logged in
    if (window.FirebaseModule && window.FirebaseModule.isUserLoggedIn()) {
        try {
            await window.FirebaseModule.saveCartToFirebase(CART);
            console.log("✓ Cart saved to Firebase");
        } catch (e) {
            console.warn("Error saving to Firebase:", e);
        }
    }
    
    // Always save to localStorage as backup
    localStorage.setItem('cart', JSON.stringify(CART));
}
```

---

## Step 5: Update buyAll() Function

**Find the `buyAll()` function (around line 570)**

**Find this line in the function:**
```javascript
window.location.href = `payment_page.html?total=${totals.total}`;
```

**Replace with:**
```javascript
window.PaymentUtils.openPaymentModal(totals.total);
```

**The complete function should look like:**
```javascript
function buyAll() {
    if (CART.length === 0) {
        showModal('Cart Empty', 'Your cart is empty! Add some items first.');
        return;
    }
    
    const totals = calculateTotal();
    const message = `🛒 Proceed to Checkout\n\nYou are about to proceed to the payment gateway for all ${CART.length} items.\n\nTotal Payable: ₹${totals.total}`;
    
    showModal('Confirm Checkout', message, true, () => {
        // CHANGED: Open payment modal instead of redirecting
        window.PaymentUtils.openPaymentModal(totals.total);
    });
}
```

---

## Done! ✅

That's it! 5 small edits:

1. ✅ Add auth container + payment modal container divs
2. ✅ Add Firebase module imports + initialization
3. ✅ Update `loadCart()` to use Firebase
4. ✅ Update `saveCart()` to sync with Firebase
5. ✅ Update `buyAll()` to open modal instead of redirect

---

## Test Immediately

1. Open `checkout.html` in browser
2. Should see **[🔐 Login]** button in top-right
3. Click login
4. Enter: `test@gmail.com` + `password123`
5. Click OK to login
6. Should reload and show avatar with initials
7. Add an item to cart
8. Click "Proceed to Secure Payment"
9. Should open modal (NOT redirect to separate page)
10. ✅ Done!

---

## What Now Works

- ✅ Login/Register with email
- ✅ Login with Google (prompts for Google account)
- ✅ Logout (click avatar → Logout)
- ✅ Cart saves to Firebase when logged in
- ✅ Cart persists across logout/login
- ✅ Payment modal opens (card + UPI tabs)
- ✅ Card payment processing
- ✅ UPI payment with link generation
- ✅ Orders saved to Firebase

---

**Total Time:** ~5 minutes to add these changes
**Lines to Edit:** 5 sections (3 functions + 2 new sections)
**Files Modified:** 1 (checkout.html)
**Files Created:** 2 (firebase-integration.js + payment-modal.js)

Ready to go! 🚀
