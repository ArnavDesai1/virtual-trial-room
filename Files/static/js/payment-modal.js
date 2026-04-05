/**
 * PAYMENT MODAL COMPONENT
 * Adapted from friend's payment_page.html
 * Creates card and UPI payment interface as a modal overlay
 */

/**
 * Create and inject the payment modal HTML + CSS into the DOM
 */
function createPaymentModal() {
    const modalHTML = `
        <div id="payment-modal" class="payment-modal" style="display: none;">
            <div class="payment-modal-content">
                <!-- Header -->
                <div class="payment-modal-header">
                    <h2>Secure Checkout</h2>
                    <p>Total Payable: <span id="payment-total-display">₹0.00</span></p>
                    <button id="payment-modal-close" class="payment-modal-close">&times;</button>
                </div>

                <!-- Tab Navigation -->
                <div class="payment-tab-navigation">
                    <button id="payment-tab-card" class="payment-tab-button active" data-tab="card-details">
                        💳 Credit/Debit Card
                    </button>
                    <button id="payment-tab-upi" class="payment-tab-button" data-tab="upi-details">
                        📱 UPI Link / ID
                    </button>
                </div>

                <!-- Modal Body -->
                <div class="payment-modal-body">
                    <!-- CARD PAYMENT TAB (from payment_page.html) -->
                    <div id="card-details" class="payment-tab-content active">
                        <form class="payment-form">
                            <!-- Card Number -->
                            <div class="payment-form-group">
                                <label for="payment-card-number">Card Number</label>
                                <input 
                                    type="text" 
                                    id="payment-card-number" 
                                    placeholder="XXXX XXXX XXXX XXXX" 
                                    maxlength="19" 
                                    class="payment-input"
                                    required
                                >
                            </div>
                            
                            <!-- Card Holder Name -->
                            <div class="payment-form-group">
                                <label for="payment-card-name">Card Holder Name</label>
                                <input 
                                    type="text" 
                                    id="payment-card-name" 
                                    placeholder="Name on Card" 
                                    class="payment-input"
                                    required
                                >
                            </div>

                            <!-- Expiry Date and CVV -->
                            <div class="payment-form-row">
                                <div class="payment-form-group">
                                    <label for="payment-expiry">Expiry (MM/YY)</label>
                                    <input 
                                        type="text" 
                                        id="payment-expiry" 
                                        placeholder="MM/YY" 
                                        maxlength="5" 
                                        class="payment-input"
                                        required
                                    >
                                </div>
                                <div class="payment-form-group">
                                    <label for="payment-cvv">CVV</label>
                                    <input 
                                        type="text" 
                                        id="payment-cvv" 
                                        placeholder="123" 
                                        maxlength="3" 
                                        class="payment-input"
                                        required
                                    >
                                </div>
                            </div>
                            
                            <button type="button" id="payment-card-submit" class="payment-button payment-button-primary">
                                💳 Process Payment
                            </button>
                        </form>
                    </div>

                    <!-- UPI PAYMENT TAB (from payment_page.html) -->
                    <div id="upi-details" class="payment-tab-content">
                        <form class="payment-form">
                            <p class="payment-form-hint">Enter your UPI ID or generate a payment link.</p>
                            
                            <!-- UPI ID Input -->
                            <div class="payment-form-group">
                                <label for="payment-upi-id">UPI ID (VPA)</label>
                                <input 
                                    type="text" 
                                    id="payment-upi-id" 
                                    placeholder="yourname@bank" 
                                    class="payment-input"
                                    required
                                >
                            </div>

                            <!-- UPI ID Payment Button -->
                            <button type="button" id="payment-upi-submit" class="payment-button payment-button-success">
                                📱 Pay with UPI ID
                            </button>
                            
                            <!-- Divider -->
                            <div class="payment-divider">
                                <span>OR</span>
                            </div>

                            <!-- Generate Link Button -->
                            <button type="button" id="payment-generate-link" class="payment-button payment-button-secondary">
                                🔗 Generate UPI Payment Link
                            </button>
                        </form>

                        <!-- Generated Link Output -->
                        <div id="payment-link-output" class="payment-link-output" style="display: none;">
                            <h4>Mock Payment Link Generated:</h4>
                            <input type="text" id="payment-link-text" readonly class="payment-link-input">
                            <button id="payment-copy-link" class="payment-button payment-button-info">
                                📋 Copy Link
                            </button>
                            <p class="payment-link-note">Note: This is a simulated link for demonstration.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <style>
            /* Payment Modal Styles */
            .payment-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.6);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                padding: 20px;
                animation: fadeInPayment 0.3s ease;
            }

            @keyframes fadeInPayment {
                from {
                    opacity: 0;
                }
                to {
                    opacity: 1;
                }
            }

            .payment-modal-content {
                background: white;
                border-radius: 16px;
                width: 100%;
                max-width: 500px;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
                animation: slideUpPayment 0.3s ease;
            }

            @keyframes slideUpPayment {
                from {
                    transform: translateY(50px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }

            .payment-modal-header {
                background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
                color: white;
                padding: 24px;
                border-radius: 16px 16px 0 0;
                position: relative;
            }

            .payment-modal-header h2 {
                font-size: 1.5rem;
                font-weight: 700;
                margin: 0 0 8px 0;
            }

            .payment-modal-header p {
                margin: 0;
                font-size: 0.95rem;
                opacity: 0.95;
            }

            .payment-modal-header p span {
                font-size: 1.3rem;
                font-weight: 700;
                margin-left: 8px;
            }

            .payment-modal-close {
                position: absolute;
                top: 16px;
                right: 16px;
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                font-size: 28px;
                cursor: pointer;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .payment-modal-close:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: rotate(90deg);
            }

            /* Tab Navigation */
            .payment-tab-navigation {
                display: flex;
                border-bottom: 1px solid #e2e8f0;
                background: #f8f9fa;
            }

            .payment-tab-button {
                flex: 1;
                padding: 16px;
                background: none;
                border: none;
                font-size: 0.95rem;
                font-weight: 600;
                color: #64748b;
                cursor: pointer;
                transition: all 0.3s;
                border-bottom: 3px solid transparent;
            }

            .payment-tab-button.active {
                color: #6366f1;
                border-bottom-color: #6366f1;
                background: white;
            }

            .payment-tab-button:hover {
                color: #6366f1;
                background: white;
            }

            /* Modal Body */
            .payment-modal-body {
                padding: 24px;
            }

            /* Tab Content */
            .payment-tab-content {
                display: none;
                animation: fadeInTab 0.3s ease;
            }

            .payment-tab-content.active {
                display: block;
            }

            @keyframes fadeInTab {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            /* Form Styles */
            .payment-form {
                display: flex;
                flex-direction: column;
                gap: 16px;
            }

            .payment-form-group {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }

            .payment-form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }

            .payment-form-group label {
                font-size: 0.875rem;
                font-weight: 600;
                color: #334155;
            }

            .payment-input {
                padding: 12px 14px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                font-size: 0.95rem;
                font-family: inherit;
                transition: all 0.2s;
            }

            .payment-input:focus {
                outline: none;
                border-color: #6366f1;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }

            .payment-form-hint {
                font-size: 0.875rem;
                color: #64748b;
                margin: 0 0 8px 0;
            }

            /* Buttons */
            .payment-button {
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                font-size: 0.95rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }

            .payment-button-primary {
                background: linear-gradient(135deg, #6366f1, #4f46e5);
                color: white;
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
            }

            .payment-button-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
            }

            .payment-button-success {
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            }

            .payment-button-success:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
            }

            .payment-button-secondary {
                background: linear-gradient(135deg, #8b5cf6, #7c3aed);
                color: white;
                box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
            }

            .payment-button-secondary:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(139, 92, 246, 0.4);
            }

            .payment-button-info {
                background: #e0e7ff;
                color: #4f46e5;
                box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
            }

            .payment-button-info:hover {
                background: #c7d2fe;
                transform: translateY(-1px);
            }

            .payment-button:active {
                transform: translateY(0);
            }

            /* Divider */
            .payment-divider {
                text-align: center;
                margin: 16px 0;
                position: relative;
                color: #94a3b8;
                font-size: 0.875rem;
            }

            .payment-divider::before {
                content: '';
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                height: 1px;
                background: #e2e8f0;
            }

            .payment-divider span {
                position: relative;
                background: white;
                padding: 0 8px;
            }

            /* Link Output */
            .payment-link-output {
                margin-top: 16px;
                padding: 16px;
                background: #f0f4f8;
                border-radius: 8px;
                border-left: 4px solid #6366f1;
            }

            .payment-link-output h4 {
                margin: 0 0 10px 0;
                font-size: 0.95rem;
                color: #4f46e5;
                font-weight: 600;
            }

            .payment-link-input {
                width: 100%;
                padding: 10px 12px;
                border: 1px dashed #cbd5e1;
                border-radius: 6px;
                font-size: 0.8rem;
                background: white;
                margin-bottom: 10px;
                font-family: monospace;
                cursor: text;
                color: #334155;
            }

            .payment-link-input:focus {
                outline: none;
                border-color: #6366f1;
            }

            .payment-link-note {
                font-size: 0.8rem;
                color: #94a3b8;
                margin: 8px 0 0 0;
            }

            /* Responsive */
            @media (max-width: 600px) {
                .payment-modal {
                    padding: 10px;
                }

                .payment-modal-content {
                    max-height: 95vh;
                }

                .payment-form-row {
                    grid-template-columns: 1fr;
                }

                .payment-tab-button {
                    font-size: 0.85rem;
                    padding: 12px;
                }

                .payment-modal-header h2 {
                    font-size: 1.2rem;
                }

                .payment-button {
                    padding: 10px 14px;
                    font-size: 0.85rem;
                }
            }
        </style>
    `;

    // Inject modal into DOM
    const container = document.getElementById('payment-modal-container');
    if (container) {
        container.innerHTML = modalHTML;
    }
}

/**
 * Initialize payment modal event listeners
 */
function initPaymentModal(FirebaseModule) {
    // Tab switching
    const tabButtons = document.querySelectorAll('.payment-tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.payment-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const contentElement = document.getElementById(tabName);
            if (contentElement) {
                contentElement.classList.add('active');
            }
        });
    });

    // Card Payment Submit
    const cardSubmitBtn = document.getElementById('payment-card-submit');
    if (cardSubmitBtn) {
        cardSubmitBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const cardNumber = document.getElementById('payment-card-number').value;
            const cardName = document.getElementById('payment-card-name').value;
            const expiry = document.getElementById('payment-expiry').value;
            const cvv = document.getElementById('payment-cvv').value;
            
            // Basic validation
            if (!cardNumber || !cardName || !expiry || !cvv) {
                alert('Please fill in all card details');
                return;
            }
            
            // Simulate payment
            cardSubmitBtn.textContent = '⏳ Processing...';
            cardSubmitBtn.disabled = true;
            
            setTimeout(async () => {
                await completePayment('card', FirebaseModule);
                cardSubmitBtn.textContent = '💳 Process Payment';
                cardSubmitBtn.disabled = false;
            }, 1500);
        });
    }

    // UPI ID Payment Submit
    const upiSubmitBtn = document.getElementById('payment-upi-submit');
    if (upiSubmitBtn) {
        upiSubmitBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const upiId = document.getElementById('payment-upi-id').value;
            
            if (!upiId) {
                alert('Please enter your UPI ID');
                return;
            }
            
            // Simulate payment
            upiSubmitBtn.textContent = '⏳ Processing...';
            upiSubmitBtn.disabled = true;
            
            setTimeout(async () => {
                await completePayment('upi', FirebaseModule);
                upiSubmitBtn.textContent = '📱 Pay with UPI ID';
                upiSubmitBtn.disabled = false;
            }, 1500);
        });
    }

    // Generate UPI Link
    const generateLinkBtn = document.getElementById('payment-generate-link');
    if (generateLinkBtn) {
        generateLinkBtn.addEventListener('click', () => {
            const linkOutput = document.getElementById('payment-link-output');
            const linkText = document.getElementById('payment-link-text');
            
            // Generate mock UPI link
            const merchantName = "VirtualTrialRoomPvtLtd";
            const mockVPA = "vtr.merchant@bank";
            const amount = getCurrentPaymentAmount();
            
            const mockLink = `upi://pay?pa=${mockVPA}&pn=${merchantName}&mc=5411&tid=VTR${Date.now()}&tr=${Date.now()}&am=${amount}&cu=INR`;
            
            linkText.value = mockLink;
            linkOutput.style.display = 'block';
            
            generateLinkBtn.textContent = '✓ Link Generated!';
            setTimeout(() => {
                generateLinkBtn.textContent = '🔗 Generate UPI Payment Link';
            }, 1500);
        });
    }

    // Copy Link to Clipboard
    const copyLinkBtn = document.getElementById('payment-copy-link');
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', () => {
            const linkText = document.getElementById('payment-link-text');
            linkText.select();
            document.execCommand('copy');
            
            copyLinkBtn.textContent = '✓ Copied!';
            setTimeout(() => {
                copyLinkBtn.textContent = '📋 Copy Link';
            }, 1500);
        });
    }

    // Close Button
    const closeBtn = document.getElementById('payment-modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closePaymentModal);
    }

    // Close on outside click
    const paymentModal = document.getElementById('payment-modal');
    if (paymentModal) {
        paymentModal.addEventListener('click', (e) => {
            if (e.target === paymentModal) {
                closePaymentModal();
            }
        });
    }
}

/**
 * Open payment modal
 */
function openPaymentModal(amount) {
    const modal = document.getElementById('payment-modal');
    if (modal) {
        // Set the amount
        document.getElementById('payment-total-display').textContent = `₹${parseFloat(amount).toFixed(2)}`;
        modal.style.display = 'flex';
    }
}

/**
 * Close payment modal
 */
function closePaymentModal() {
    const modal = document.getElementById('payment-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Get current payment amount
 */
function getCurrentPaymentAmount() {
    const display = document.getElementById('payment-total-display');
    return display ? display.textContent.replace('₹', '').trim() : '0.00';
}

/**
 * Complete payment and save to Firebase
 */
async function completePayment(method, FirebaseModule) {
    const amount = getCurrentPaymentAmount();
    
    // Show success message
    alert(`✓ Payment of ₹${amount} completed via ${method === 'card' ? 'Card' : 'UPI'}!`);
    
    // Save purchase to Firebase if user is logged in
    if (FirebaseModule.isUserLoggedIn()) {
        const orderData = {
            items: getCartItems?.() || [],  // This should be connected to checkout's cart
            amount: parseFloat(amount),
            paymentMethod: method,
            status: 'completed'
        };
        
        await FirebaseModule.savePurchase(orderData);
    }
    
    // Close modal
    closePaymentModal();
    
    // Redirect or refresh as needed
    setTimeout(() => {
        window.location.reload();
    }, 1000);
}

// ============================================================================
// Export Functions
// ============================================================================
export {
    createPaymentModal,
    initPaymentModal,
    openPaymentModal,
    closePaymentModal,
    getCurrentPaymentAmount
};
