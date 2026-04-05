/**
 * Firebase Authentication & Data Management Module
 * Centralized auth handling for E-Dressing Room
 */

import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signOut,
    onAuthStateChanged,
    GoogleAuthProvider,
    signInWithPopup
} from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";
import {
    getFirestore,
    collection,
    addDoc,
    query,
    where,
    getDocs,
    setDoc,
    doc,
    getDoc
} from "https://www.gstatic.com/firebasejs/9.6.1/firebase-firestore.js";

// ============================================================================
// FIREBASE CONFIGURATION
// ============================================================================

const firebaseConfig = {
    apiKey: "AIzaSyCfaeh8cB_vkL17FLd9qIAYXQywLBAHkqM",
    authDomain: "virtual-trial-room-3cff3.firebaseapp.com",
    projectId: "virtual-trial-room-3cff3",
    storageBucket: "virtual-trial-room-3cff3.firebasestorage.app",
    messagingSenderId: "678744292818",
    appId: "1:678744292818:web:a31747dd608d86b21f1c0b",
    measurementId: "G-10TCLDZE4X"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// ============================================================================
// GLOBAL STATE MANAGEMENT
// ============================================================================

let currentUser = null;
let authStateCallbacks = [];

// ============================================================================
// AUTH STATE LISTENER
// ============================================================================

onAuthStateChanged(auth, async (user) => {
    currentUser = user;
    
    // Trigger all callbacks registered for auth state changes
    authStateCallbacks.forEach(callback => callback(user));
    
    // Dispatch custom event for other parts of the app
    window.dispatchEvent(new CustomEvent('authStateChanged', { detail: user }));
    
    // Update UI based on auth state
    updateAuthUI(user);
    
    if (user) {
        console.log('User logged in:', user.email);
        // Load user's cart and purchase history from Firebase
        await loadUserData(user.uid);
    } else {
        console.log('User logged out');
    }
});

// ============================================================================
// PUBLIC API FUNCTIONS
// ============================================================================

/**
 * Register a new user with email and password
 */
export async function registerWithEmail(email, password) {
    try {
        if (!isValidAndAllowedEmail(email)) {
            throw new Error('Email domain not allowed. Use gmail.com, yahoo.com, outlook.com, or somaiya.edu');
        }
        if (password.length < 6) {
            throw new Error('Password must be at least 6 characters long');
        }
        
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        
        // Create user profile in Firestore
        await setDoc(doc(db, 'users', userCredential.user.uid), {
            email: email,
            displayName: email.split('@')[0],
            createdAt: new Date(),
            cart: [],
            purchases: []
        });
        
        return { success: true, user: userCredential.user };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Login with email and password
 */
export async function loginWithEmail(email, password) {
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        return { success: true, user: userCredential.user };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Sign in with Google
 */
export async function loginWithGoogle() {
    try {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        
        // Create or update user profile in Firestore
        const userRef = doc(db, 'users', result.user.uid);
        const userSnap = await getDoc(userRef);
        
        if (!userSnap.exists()) {
            await setDoc(userRef, {
                email: result.user.email,
                displayName: result.user.displayName || result.user.email.split('@')[0],
                photoURL: result.user.photoURL,
                createdAt: new Date(),
                cart: [],
                purchases: []
            });
        }
        
        return { success: true, user: result.user };
    } catch (error) {
        if (error.code === 'auth/popup-closed-by-user') {
            return { success: false, error: 'Google Sign-In was cancelled' };
        }
        return { success: false, error: error.message };
    }
}

/**
 * Logout current user
 */
export async function logout() {
    try {
        await signOut(auth);
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Get current user
 */
export function getCurrentUser() {
    return currentUser;
}

/**
 * Check if user is logged in
 */
export function isUserLoggedIn() {
    return currentUser !== null;
}

/**
 * Register callback for auth state changes
 */
export function onAuthStateChange(callback) {
    authStateCallbacks.push(callback);
    
    // Immediately call with current state
    if (currentUser !== null) {
        callback(currentUser);
    }
}

// ============================================================================
// CART MANAGEMENT
// ============================================================================

/**
 * Save cart to Firebase
 */
export async function saveCartToFirebase(cartData) {
    if (!currentUser) {
        // If not logged in, save to localStorage only
        localStorage.setItem('cart', JSON.stringify(cartData));
        return { success: true, message: 'Cart saved locally' };
    }
    
    try {
        const userRef = doc(db, 'users', currentUser.uid);
        await setDoc(userRef, { cart: cartData }, { merge: true });
        localStorage.setItem('cart', JSON.stringify(cartData));
        return { success: true, message: 'Cart saved to Firebase' };
    } catch (error) {
        console.error('Error saving cart:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Load user's cart from Firebase
 */
export async function loadCartFromFirebase() {
    if (!currentUser) {
        // Load from localStorage if not logged in
        const savedCart = localStorage.getItem('cart');
        return savedCart ? JSON.parse(savedCart) : [];
    }
    
    try {
        const userRef = doc(db, 'users', currentUser.uid);
        const userSnap = await getDoc(userRef);
        
        if (userSnap.exists() && userSnap.data().cart) {
            const firebaseCart = userSnap.data().cart;
            localStorage.setItem('cart', JSON.stringify(firebaseCart));
            return firebaseCart;
        }
        return [];
    } catch (error) {
        console.error('Error loading cart:', error);
        return [];
    }
}

// ============================================================================
// PURCHASE HISTORY
// ============================================================================

/**
 * Save a purchase/order
 */
export async function savePurchase(orderData) {
    if (!currentUser) {
        return { success: false, error: 'User must be logged in to save purchases' };
    }
    
    try {
        const purchaseRef = collection(db, 'users', currentUser.uid, 'purchases');
        const docRef = await addDoc(purchaseRef, {
            ...orderData,
            purchaseDate: new Date(),
            status: 'completed'
        });
        
        return { success: true, purchaseId: docRef.id };
    } catch (error) {
        console.error('Error saving purchase:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Get user's purchase history
 */
export async function getPurchaseHistory() {
    if (!currentUser) {
        return [];
    }
    
    try {
        const purchasesRef = collection(db, 'users', currentUser.uid, 'purchases');
        const q = query(purchasesRef); // Get all purchases for this user
        const querySnapshot = await getDocs(q);
        
        const purchases = [];
        querySnapshot.forEach((doc) => {
            purchases.push({
                id: doc.id,
                ...doc.data()
            });
        });
        
        return purchases.sort((a, b) => b.purchaseDate - a.purchaseDate);
    } catch (error) {
        console.error('Error getting purchase history:', error);
        return [];
    }
}

/**
 * Add item to purchase history as "previously bought"
 */
export async function addToPreviousBought(itemData) {
    if (!currentUser) {
        return { success: false, error: 'User must be logged in' };
    }
    
    try {
        const previousBoughtRef = collection(db, 'users', currentUser.uid, 'previouslyBought');
        const docRef = await addDoc(previousBoughtRef, {
            ...itemData,
            addedDate: new Date()
        });
        
        return { success: true, itemId: docRef.id };
    } catch (error) {
        console.error('Error adding to previously bought:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Get previously bought items
 */
export async function getPreviouslyBought() {
    if (!currentUser) {
        return [];
    }
    
    try {
        const previousBoughtRef = collection(db, 'users', currentUser.uid, 'previouslyBought');
        const querySnapshot = await getDocs(previousBoughtRef);
        
        const items = [];
        querySnapshot.forEach((doc) => {
            items.push({
                id: doc.id,
                ...doc.data()
            });
        });
        
        return items;
    } catch (error) {
        console.error('Error getting previously bought items:', error);
        return [];
    }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Validate email format and domain
 */
function isValidAndAllowedEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return false;
    }
    
    const allowedDomains = ['gmail.com', 'yahoo.com', 'outlook.com', 'somaiya.edu'];
    const domain = email.substring(email.lastIndexOf('@') + 1).toLowerCase();
    return allowedDomains.includes(domain);
}

/**
 * Load user data from Firebase (cart, purchases, etc.)
 */
async function loadUserData(uid) {
    try {
        // Load cart
        const userRef = doc(db, 'users', uid);
        const userSnap = await getDoc(userRef);
        
        if (userSnap.exists() && userSnap.data().cart) {
            localStorage.setItem('cart', JSON.stringify(userSnap.data().cart));
            // Trigger cart update event
            window.dispatchEvent(new CustomEvent('cartUpdated', { 
                detail: userSnap.data().cart 
            }));
        }
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

/**
 * Update UI based on auth state
 */
function updateAuthUI(user) {
    const authContainer = document.getElementById('auth-container');
    if (!authContainer) return;
    
    if (user) {
        // Show user avatar and details
        authContainer.innerHTML = `
            <div class="user-profile-container">
                <div class="user-avatar" id="user-avatar-btn" title="Click for profile menu">
                    ${getAvatarInitials(user.displayName || user.email)}
                </div>
                <div class="user-menu hidden" id="user-menu">
                    <div class="user-menu-header">
                        <div class="user-avatar-large">
                            ${getAvatarInitials(user.displayName || user.email)}
                        </div>
                        <div class="user-info">
                            <div class="user-name">${user.displayName || 'User'}</div>
                            <div class="user-email">${user.email}</div>
                        </div>
                    </div>
                    <hr>
                    <button id="logout-btn" class="logout-button">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </button>
                </div>
            </div>
        `;
        
        // Add event listeners
        const avatarBtn = document.getElementById('user-avatar-btn');
        const userMenu = document.getElementById('user-menu');
        const logoutBtn = document.getElementById('logout-btn');
        
        if (avatarBtn && userMenu) {
            avatarBtn.addEventListener('click', () => {
                userMenu.classList.toggle('hidden');
            });
            
            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!authContainer.contains(e.target)) {
                    userMenu.classList.add('hidden');
                }
            });
        }
        
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                const result = await logout();
                if (result.success) {
                    userMenu.classList.add('hidden');
                    // Redirect or reload
                    window.location.href = '/';
                }
            });
        }
    } else {
        // Show login/register button
        authContainer.innerHTML = `
            <button id="auth-btn" class="auth-button">
                <i class="fas fa-sign-in-alt"></i> Login / Register
            </button>
        `;
        
        const authBtn = document.getElementById('auth-btn');
        if (authBtn) {
            authBtn.addEventListener('click', () => {
                openAuthModal();
            });
        }
    }
}

/**
 * Get avatar initials from name/email
 */
function getAvatarInitials(text) {
    if (!text) return '?';
    const parts = text.split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return text.substring(0, 2).toUpperCase();
}

/**
 * Open authentication modal
 */
export function openAuthModal() {
    // This will be called from the page to show auth modal
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.style.display = 'block';
    }
}

/**
 * Close authentication modal
 */
export function closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ============================================================================
// EXPORT ALL FUNCTIONS
// ============================================================================

export default {
    registerWithEmail,
    loginWithEmail,
    loginWithGoogle,
    logout,
    getCurrentUser,
    isUserLoggedIn,
    onAuthStateChange,
    saveCartToFirebase,
    loadCartFromFirebase,
    savePurchase,
    getPurchaseHistory,
    addToPreviousBought,
    getPreviouslyBought,
    openAuthModal,
    closeAuthModal
};
