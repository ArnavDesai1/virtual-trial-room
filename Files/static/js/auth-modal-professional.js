/**
 * PROFESSIONAL AUTH MODAL
 * Clean, modern design like ChatGPT
 * Email/Password + Google Sign-In
 */

function createAuthModal() {
    const modalHTML = `
        <div id="auth-modal-overlay" style="
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 10001;
            backdrop-filter: blur(4px);
        "></div>
        
        <div id="auth-modal" style="
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 95%;
            max-width: 450px;
            max-height: 90vh;
            overflow-y: auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            z-index: 10002;
            animation: slideUp 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        ">
            <!-- Close Button -->
            <button id="auth-modal-close" style="
                position: absolute;
                top: 16px;
                right: 16px;
                width: 32px;
                height: 32px;
                background: #f0f0f0;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                font-size: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            ">×</button>
            
            <!-- Header -->
            <div style="
                padding: 32px 32px 24px;
                border-bottom: 1px solid #e5e5e5;
            ">
                <h2 style="
                    margin: 0 0 8px 0;
                    font-size: 24px;
                    font-weight: 600;
                    color: #000;
                " id="auth-modal-title">Welcome Back</h2>
                <p style="
                    margin: 0;
                    font-size: 14px;
                    color: #666;
                " id="auth-modal-subtitle">Sign in to your account</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 32px;">
                
                <!-- Email/Password Form -->
                <form id="auth-form" style="display: block;">
                    <!-- Email Input -->
                    <div style="margin-bottom: 16px;">
                        <label style="
                            display: block;
                            font-size: 14px;
                            font-weight: 500;
                            margin-bottom: 6px;
                            color: #000;
                        ">Email Address</label>
                        <input id="auth-email" type="email" placeholder="you@example.com" style="
                            width: 100%;
                            padding: 12px 14px;
                            border: 1px solid #d0d0d0;
                            border-radius: 8px;
                            font-size: 14px;
                            font-family: inherit;
                            box-sizing: border-box;
                            transition: border-color 0.2s;
                        " required>
                    </div>
                    
                    <!-- Password Input -->
                    <div style="margin-bottom: 24px;">
                        <label style="
                            display: block;
                            font-size: 14px;
                            font-weight: 500;
                            margin-bottom: 6px;
                            color: #000;
                        ">Password</label>
                        <input id="auth-password" type="password" placeholder="••••••••" style="
                            width: 100%;
                            padding: 12px 14px;
                            border: 1px solid #d0d0d0;
                            border-radius: 8px;
                            font-size: 14px;
                            font-family: inherit;
                            box-sizing: border-box;
                            transition: border-color 0.2s;
                        " required minlength="6">
                    </div>
                    
                    <!-- Submit Button -->
                    <button type="submit" style="
                        width: 100%;
                        padding: 12px 16px;
                        background: #10a37f;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 15px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: background 0.2s;
                        margin-bottom: 16px;
                    " id="auth-submit-btn">Sign In</button>
                </form>
                
                <!-- Divider -->
                <div style="
                    display: flex;
                    align-items: center;
                    margin: 24px 0;
                    gap: 12px;
                ">
                    <div style="flex: 1; height: 1px; background: #e5e5e5;"></div>
                    <span style="color: #999; font-size: 13px;">OR</span>
                    <div style="flex: 1; height: 1px; background: #e5e5e5;"></div>
                </div>
                
                <!-- Social Login Buttons - ChatGPT Style -->
                <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px;">
                    <!-- Google Sign-In -->
                    <button id="auth-google-btn" style="
                        width: 100%;
                        padding: 12px 16px;
                        background: white;
                        border: 1px solid #d0d0d0;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: 500;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 10px;
                        transition: all 0.2s;
                    ">
                        <svg width="18" height="18" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        Continue with Google
                    </button>
                    
                    <!-- Apple Sign-In -->
                    <button id="auth-apple-btn" style="
                        width: 100%;
                        padding: 12px 16px;
                        background: #000;
                        color: white;
                        border: 1px solid #000;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: 500;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 10px;
                        transition: all 0.2s;
                    ">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
                            <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57.22-.78.36-1.53.08zm-3.03-16.5c.15-1.09 1.14-2.03 2.31-2.15.15 1.09-.88 2.02-2.31 2.15z"/>
                        </svg>
                        Continue with Apple
                    </button>
                    
                    <!-- Microsoft Sign-In -->
                    <button id="auth-microsoft-btn" style="
                        width: 100%;
                        padding: 12px 16px;
                        background: white;
                        border: 1px solid #d0d0d0;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: 500;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 10px;
                        transition: all 0.2s;
                    ">
                        <svg width="18" height="18" viewBox="0 0 24 24">
                            <path fill="#F25022" d="M1 1h10v10H1z"/>
                            <path fill="#7FBA00" d="M13 1h10v10H13z"/>
                            <path fill="#00A4EF" d="M1 13h10v10H1z"/>
                            <path fill="#FFB900" d="M13 13h10v10H13z"/>
                        </svg>
                        Continue with Microsoft
                    </button>
                    
                    <!-- Phone Sign-In -->
                    <button id="auth-phone-btn" style="
                        width: 100%;
                        padding: 12px 16px;
                        background: white;
                        border: 1px solid #d0d0d0;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: 500;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 10px;
                        transition: all 0.2s;
                    ">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                        </svg>
                        Continue with phone
                    </button>
                </div>
                
                <!-- Toggle Button -->
                <div style="text-align: center;">
                    <button id="auth-toggle-btn" type="button" style="
                        background: none;
                        border: none;
                        color: #10a37f;
                        cursor: pointer;
                        font-size: 14px;
                        text-decoration: none;
                        font-weight: 500;
                    "></button>
                </div>
            </div>
        </div>
        
        <style>
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translate(-50%, -45%);
                }
                to {
                    opacity: 1;
                    transform: translate(-50%, -50%);
                }
            }
            
            #auth-email:focus,
            #auth-password:focus {
                outline: none;
                border-color: #10a37f;
                box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1);
            }
            
            #auth-submit-btn:hover {
                background: #0d8e6f;
            }
            
            #auth-google-btn:hover,
            #auth-microsoft-btn:hover,
            #auth-phone-btn:hover {
                background: #f9f9f9;
                border-color: #b0b0b0;
            }
            
            #auth-apple-btn:hover {
                background: #1a1a1a;
            }
            
            #auth-modal-close:hover {
                background: #e0e0e0;
            }
        </style>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Mode tracking
    let isLoginMode = true;
    
    // Get elements
    const modal = document.getElementById('auth-modal');
    const overlay = document.getElementById('auth-modal-overlay');
    const closeBtn = document.getElementById('auth-modal-close');
    const form = document.getElementById('auth-form');
    const emailInput = document.getElementById('auth-email');
    const passwordInput = document.getElementById('auth-password');
    const submitBtn = document.getElementById('auth-submit-btn');
    const googleBtn = document.getElementById('auth-google-btn');
    const toggleBtn = document.getElementById('auth-toggle-btn');
    const title = document.getElementById('auth-modal-title');
    const subtitle = document.getElementById('auth-modal-subtitle');
    
    // Update toggle button text
    function updateToggleBtn() {
        toggleBtn.textContent = isLoginMode ? 
            "Don't have an account? Sign Up" : 
            "Already have an account? Sign In";
    }
    updateToggleBtn();
    
    // Close modal
    function closeAuthModal() {
        modal.style.display = 'none';
        overlay.style.display = 'none';
        form.reset();
        isLoginMode = true;
        updateToggleBtn();
    }
    
    // Open modal
    window.openAuthModal = function(mode = 'login') {
        isLoginMode = mode === 'login';
        title.textContent = isLoginMode ? 'Welcome Back' : 'Create Account';
        subtitle.textContent = isLoginMode ? 'Sign in to your account' : 'Join us today';
        submitBtn.textContent = isLoginMode ? 'Sign In' : 'Create Account';
        updateToggleBtn();
        modal.style.display = 'block';
        overlay.style.display = 'block';
        emailInput.focus();
    };
    
    // Event listeners
    closeBtn.addEventListener('click', closeAuthModal);
    overlay.addEventListener('click', closeAuthModal);
    modal.addEventListener('click', (e) => e.stopPropagation());
    
    // Toggle between login and register
    toggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        isLoginMode = !isLoginMode;
        title.textContent = isLoginMode ? 'Welcome Back' : 'Create Account';
        subtitle.textContent = isLoginMode ? 'Sign in to your account' : 'Join us today';
        submitBtn.textContent = isLoginMode ? 'Sign In' : 'Create Account';
        updateToggleBtn();
        form.reset();
        emailInput.focus();
    });
    
    // Form submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        
        if (!email || !password) {
            alert('Please fill in all fields');
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Please wait...';
        
        try {
            let result;
            if (isLoginMode) {
                result = await window.FirebaseModule.loginWithEmail(email, password);
            } else {
                result = await window.FirebaseModule.registerWithEmail(email, password);
            }
            
            if (result.success) {
                alert('✅ ' + result.message);
                closeAuthModal();
                window.location.reload();
            } else {
                alert('❌ Error: ' + result.error);
            }
        } catch (error) {
            alert('❌ An error occurred: ' + error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = isLoginMode ? 'Sign In' : 'Create Account';
        }
    });
    
    // Google Sign-In
    googleBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        googleBtn.disabled = true;
        googleBtn.textContent = 'Signing in...';
        
        try {
            const result = await window.FirebaseModule.loginWithGoogle();
            if (result.success) {
                alert('✅ ' + result.message);
                closeAuthModal();
                window.location.reload();
            } else {
                alert('❌ Error: ' + result.error);
            }
        } catch (error) {
            alert('❌ An error occurred: ' + error.message);
        } finally {
            googleBtn.disabled = false;
            googleBtn.textContent = 'Continue with Google';
        }
    });
    
    // Apple Sign-In (placeholder - disabled since only using Google)
    const appleBtn = document.getElementById('auth-apple-btn');
    if (appleBtn) {
        appleBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            alert('🍎 Apple Sign-In is not configured.\n\nPlease use Google Sign-In.');
        });
    }
    
    // Microsoft Sign-In (placeholder - disabled since only using Google)
    const microsoftBtn = document.getElementById('auth-microsoft-btn');
    if (microsoftBtn) {
        microsoftBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            alert('🔷 Microsoft Sign-In is not configured.\n\nPlease use Google Sign-In.');
        });
    }
    
    // Phone Sign-In (placeholder - disabled since only using Google)
    const phoneBtn = document.getElementById('auth-phone-btn');
    if (phoneBtn) {
        phoneBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            alert('📱 Phone Sign-In is not configured.\n\nPlease use Google Sign-In.');
        });
    }
}

// Export
export { createAuthModal };
