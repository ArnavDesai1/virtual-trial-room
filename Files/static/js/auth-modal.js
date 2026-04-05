/**
 * Authentication Modal Component
 * Provides login, register, and Google Sign-In functionality
 */

export function createAuthModal() {
    const modalHTML = `
        <!-- AUTH MODAL OVERLAY -->
        <div id="auth-modal" class="auth-modal hidden">
            <div class="auth-modal-content">
                <!-- Close Button -->
                <button id="auth-modal-close" class="auth-modal-close">
                    <i class="fas fa-times"></i>
                </button>

                <!-- Modal Header -->
                <div class="auth-modal-header">
                    <h1 class="auth-modal-title">
                        <i class="fas fa-tshirt"></i> E-Dressing Room
                    </h1>
                    <p class="auth-modal-subtitle">Create an account or login to continue</p>
                </div>

                <!-- Tab Navigation -->
                <div class="auth-tabs">
                    <button class="auth-tab-btn active" data-tab="login">
                        <i class="fas fa-sign-in-alt"></i> Login
                    </button>
                    <button class="auth-tab-btn" data-tab="register">
                        <i class="fas fa-user-plus"></i> Register
                    </button>
                </div>

                <!-- LOGIN TAB -->
                <div id="login-tab" class="auth-tab-content active">
                    <form id="login-form" class="auth-form">
                        <div class="form-group">
                            <label for="login-email">Email Address</label>
                            <input 
                                id="login-email" 
                                type="email" 
                                placeholder="your@email.com" 
                                required
                                autocomplete="email"
                            >
                            <span class="form-error" id="login-email-error"></span>
                        </div>

                        <div class="form-group">
                            <label for="login-password">Password</label>
                            <input 
                                id="login-password" 
                                type="password" 
                                placeholder="Enter your password" 
                                required
                                autocomplete="current-password"
                            >
                            <span class="form-error" id="login-password-error"></span>
                        </div>

                        <button type="submit" id="login-submit-btn" class="auth-submit-btn">
                            <i class="fas fa-sign-in-alt"></i> Sign In
                        </button>

                        <div class="form-error" id="login-error" style="text-align: center; margin-top: 12px;"></div>
                        <div class="form-success" id="login-success" style="text-align: center; margin-top: 12px;"></div>
                    </form>
                </div>

                <!-- REGISTER TAB -->
                <div id="register-tab" class="auth-tab-content hidden">
                    <form id="register-form" class="auth-form">
                        <div class="form-group">
                            <label for="register-email">Email Address</label>
                            <input 
                                id="register-email" 
                                type="email" 
                                placeholder="your@email.com" 
                                required
                                autocomplete="email"
                            >
                            <span class="form-error" id="register-email-error"></span>
                            <small class="form-hint">Use gmail.com, yahoo.com, outlook.com, or somaiya.edu</small>
                        </div>

                        <div class="form-group">
                            <label for="register-password">Password</label>
                            <input 
                                id="register-password" 
                                type="password" 
                                placeholder="At least 6 characters" 
                                required
                                autocomplete="new-password"
                            >
                            <span class="form-error" id="register-password-error"></span>
                            <small class="form-hint">Minimum 6 characters required</small>
                        </div>

                        <div class="form-group">
                            <label for="register-confirm">Confirm Password</label>
                            <input 
                                id="register-confirm" 
                                type="password" 
                                placeholder="Confirm your password" 
                                required
                                autocomplete="new-password"
                            >
                            <span class="form-error" id="register-confirm-error"></span>
                        </div>

                        <button type="submit" id="register-submit-btn" class="auth-submit-btn">
                            <i class="fas fa-user-plus"></i> Create Account
                        </button>

                        <div class="form-error" id="register-error" style="text-align: center; margin-top: 12px;"></div>
                        <div class="form-success" id="register-success" style="text-align: center; margin-top: 12px;"></div>
                    </form>
                </div>

                <!-- DIVIDER -->
                <div class="auth-divider">
                    <span>OR</span>
                </div>

                <!-- GOOGLE SIGN-IN (VISIBLE IN BOTH TABS) -->
                <button id="google-signin-btn" class="google-signin-btn">
                    <svg class="google-icon" viewBox="0 0 24 24">
                        <path fill="#1f2937" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#1f2937" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#1f2937" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#1f2937" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Continue with Google
                </button>
            </div>
        </div>

        <!-- AUTH MODAL STYLES -->
        <style>
            /* Modal Container */
            .auth-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.6);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 3000;
                padding: 20px;
                animation: fadeIn 0.3s ease-out;
            }

            .auth-modal.hidden {
                display: none !important;
            }

            @keyframes fadeIn {
                from {
                    opacity: 0;
                }
                to {
                    opacity: 1;
                }
            }

            /* Modal Content */
            .auth-modal-content {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                width: 100%;
                max-width: 420px;
                padding: 40px;
                position: relative;
                animation: slideUp 0.3s ease-out;
            }

            @keyframes slideUp {
                from {
                    transform: translateY(40px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }

            /* Close Button */
            .auth-modal-close {
                position: absolute;
                top: 16px;
                right: 16px;
                width: 40px;
                height: 40px;
                border: none;
                background: #f3f4f6;
                border-radius: 50%;
                cursor: pointer;
                font-size: 20px;
                color: #6b7280;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .auth-modal-close:hover {
                background: #e5e7eb;
                color: #1f2937;
            }

            /* Header */
            .auth-modal-header {
                text-align: center;
                margin-bottom: 30px;
            }

            .auth-modal-title {
                font-size: 24px;
                font-weight: 800;
                color: #1f2937;
                margin: 0 0 8px 0;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }

            .auth-modal-title i {
                font-size: 28px;
                background: linear-gradient(135deg, #6366f1, #ec4899);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .auth-modal-subtitle {
                font-size: 14px;
                color: #6b7280;
                margin: 0;
            }

            /* Tabs */
            .auth-tabs {
                display: flex;
                gap: 12px;
                margin-bottom: 30px;
                border-bottom: 2px solid #f3f4f6;
            }

            .auth-tab-btn {
                flex: 1;
                padding: 12px;
                border: none;
                background: none;
                font-size: 14px;
                font-weight: 600;
                color: #6b7280;
                cursor: pointer;
                border-bottom: 3px solid transparent;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
            }

            .auth-tab-btn.active {
                color: #6366f1;
                border-bottom-color: #6366f1;
            }

            .auth-tab-btn:hover {
                color: #374151;
            }

            /* Tab Content */
            .auth-tab-content {
                display: none;
            }

            .auth-tab-content.active {
                display: block;
                animation: fadeIn 0.3s ease-out;
            }

            /* Form */
            .auth-form {
                display: flex;
                flex-direction: column;
                gap: 16px;
            }

            .form-group {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }

            .form-group label {
                font-size: 13px;
                font-weight: 600;
                color: #374151;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .form-group input {
                padding: 12px 14px;
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                font-size: 14px;
                font-family: inherit;
                transition: all 0.3s ease;
            }

            .form-group input:focus {
                outline: none;
                border-color: #6366f1;
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }

            .form-group input::placeholder {
                color: #d1d5db;
            }

            .form-hint {
                font-size: 12px;
                color: #9ca3af;
                margin-top: 4px;
            }

            .form-error {
                font-size: 12px;
                color: #ef4444;
                display: none;
            }

            .form-error.show {
                display: block;
            }

            .form-success {
                font-size: 13px;
                color: #10b981;
                font-weight: 600;
                display: none;
            }

            .form-success.show {
                display: block;
            }

            /* Submit Button */
            .auth-submit-btn {
                padding: 12px 20px;
                background: linear-gradient(135deg, #6366f1, #ec4899);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
            }

            .auth-submit-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
            }

            .auth-submit-btn:active {
                transform: translateY(0);
            }

            .auth-submit-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            /* Divider */
            .auth-divider {
                display: flex;
                align-items: center;
                gap: 12px;
                margin: 24px 0;
                color: #d1d5db;
                font-size: 13px;
            }

            .auth-divider::before,
            .auth-divider::after {
                content: '';
                flex: 1;
                height: 1px;
                background: #e5e7eb;
            }

            /* Google Sign-In Button */
            .google-signin-btn {
                width: 100%;
                padding: 12px 20px;
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                color: #374151;
            }

            .google-signin-btn:hover {
                border-color: #6366f1;
                background: #f9fafb;
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
            }

            .google-icon {
                width: 18px;
                height: 18px;
            }

            /* Responsive */
            @media (max-width: 480px) {
                .auth-modal-content {
                    padding: 30px 20px;
                    max-width: 100%;
                }

                .auth-modal-title {
                    font-size: 20px;
                }

                .auth-tabs {
                    margin-bottom: 24px;
                }

                .auth-submit-btn {
                    padding: 10px 16px;
                    font-size: 13px;
                }
            }
        </style>
    `;

    return modalHTML;
}

/**
 * Initialize auth modal and attach event listeners
 */
export function initAuthModal(authModule) {
    const modal = document.getElementById('auth-modal');
    if (!modal) return;

    // Tab switching
    document.querySelectorAll('.auth-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabName = e.currentTarget.dataset.tab;
            
            // Update button states
            document.querySelectorAll('.auth-tab-btn').forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            
            // Update content visibility
            document.querySelectorAll('.auth-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });

    // Close button
    document.getElementById('auth-modal-close').addEventListener('click', () => {
        authModule.closeAuthModal();
    });

    // Close when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            authModule.closeAuthModal();
        }
    });

    // LOGIN FORM
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value;
            const submitBtn = document.getElementById('login-submit-btn');
            const errorDiv = document.getElementById('login-error');
            const successDiv = document.getElementById('login-success');

            // Clear previous messages
            errorDiv.classList.remove('show');
            successDiv.classList.remove('show');

            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';

            const result = await authModule.loginWithEmail(email, password);

            if (result.success) {
                successDiv.textContent = '✓ Login successful! Redirecting...';
                successDiv.classList.add('show');
                setTimeout(() => {
                    authModule.closeAuthModal();
                    loginForm.reset();
                }, 1500);
            } else {
                errorDiv.textContent = '✗ ' + result.error;
                errorDiv.classList.add('show');
            }

            // Reset button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
        });
    }

    // REGISTER FORM
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('register-email').value.trim();
            const password = document.getElementById('register-password').value;
            const confirmPassword = document.getElementById('register-confirm').value;
            const submitBtn = document.getElementById('register-submit-btn');
            const errorDiv = document.getElementById('register-error');
            const successDiv = document.getElementById('register-success');

            // Clear previous messages
            errorDiv.classList.remove('show');
            successDiv.classList.remove('show');

            // Validation
            if (password !== confirmPassword) {
                errorDiv.textContent = '✗ Passwords do not match';
                errorDiv.classList.add('show');
                return;
            }

            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';

            const result = await authModule.registerWithEmail(email, password);

            if (result.success) {
                successDiv.textContent = '✓ Account created! Please log in.';
                successDiv.classList.add('show');
                setTimeout(() => {
                    registerForm.reset();
                    document.querySelector('[data-tab="login"]').click();
                }, 1500);
            } else {
                errorDiv.textContent = '✗ ' + result.error;
                errorDiv.classList.add('show');
            }

            // Reset button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
        });
    }

    // GOOGLE SIGN-IN
    const googleBtn = document.getElementById('google-signin-btn');
    if (googleBtn) {
        googleBtn.addEventListener('click', async () => {
            googleBtn.disabled = true;
            googleBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';

            const result = await authModule.loginWithGoogle();

            if (result.success) {
                authModule.closeAuthModal();
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                alert('Google Sign-In Error: ' + result.error);
            }

            googleBtn.disabled = false;
            googleBtn.innerHTML = '<i class="fab fa-google"></i> Continue with Google';
        });
    }
}
