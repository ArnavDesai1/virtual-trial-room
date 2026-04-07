/**
 * FIREBASE INTEGRATION MODULE
 * Uses authentication code from friend's auth.html
 * Extends it with cart, purchase history, and unified auth state management
 */

// ============================================================================
// 1. FIREBASE INITIALIZATION (From auth.html)
// ============================================================================
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import {
    getAuth,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup,
    signOut,
    onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/9.6.1/firebase-auth.js";
import {
    getFirestore,
    collection,
    doc,
    setDoc,
    getDoc,
    updateDoc,
    addDoc,
    query,
    where,
    getDocs,
    serverTimestamp
} from "https://www.gstatic.com/firebasejs/9.6.1/firebase-firestore.js";

// Fetch Firebase config from backend (secure - key not exposed in frontend)
let app, auth, db;

async function initializeFirebase() {
    try {
        const response = await fetch('/api/firebase-config');
        if (!response.ok) throw new Error('Failed to fetch Firebase config');
        const firebaseConfig = await response.json();
        
        app = initializeApp(firebaseConfig);
        auth = getAuth(app);
        db = getFirestore(app);
        
        console.log('Firebase initialized successfully');
        return { app, auth, db };
    } catch (error) {
        console.error('Firebase initialization failed:', error);
        // Fallback config (for demo purposes)
        const firebaseConfig = {
            apiKey: "",
            authDomain: "virtual-trial-room-3cff3.firebaseapp.com",
            projectId: "virtual-trial-room-3cff3",
            storageBucket: "virtual-trial-room-3cff3.firebasestorage.app",
            messagingSenderId: "678744292818",
            appId: "1:678744292818:web:a31747dd608d86b21f1c0b",
            measurementId: "G-10TCLDZE4X"
        };
        app = initializeApp(firebaseConfig);
        auth = getAuth(app);
        db = getFirestore(app);
        return { app, auth, db };
    }
}

// Initialize Firebase
await initializeFirebase();

// ============================================================================
// 2. GLOBAL AUTH STATE
// ============================================================================
let currentUser = null;
const authStateCallbacks = [];
const ALLOWED_EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "somaiya.edu"];

// Sync pending user documents when connection is restored
async function syncPendingUserDocuments() {
    const keys = Object.keys(localStorage).filter(key => key.startsWith('pending_user_'));
    for (const key of keys) {
        try {
            const pendingUser = JSON.parse(localStorage.getItem(key));
            const uid = pendingUser.uid;
            delete pendingUser.uid;
            
            const userDoc = await getDoc(doc(db, "users", uid));
            if (!userDoc.exists()) {
                await setDoc(doc(db, "users", uid), {
                    ...pendingUser,
                    createdAt: serverTimestamp()
                });
                localStorage.removeItem(key);
                console.log("Synced pending user document:", uid);
            }
        } catch (error) {
            // Silently fail - will retry later
            console.log("Could not sync pending user:", error.message);
        }
    }
}

// ============================================================================
// 3. EMAIL VALIDATION (From auth.html)
// ============================================================================
function isValidAndAllowedEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) return false;
    
    const domain = email.substring(email.lastIndexOf('@') + 1).toLowerCase();
    return ALLOWED_EMAIL_DOMAINS.includes(domain);
}

// ============================================================================
// 4. AUTHENTICATION FUNCTIONS (From auth.html + Enhanced)
// ============================================================================

/**
 * Register user with email and password
 * Validates domain before Firebase registration
 */
async function registerWithEmail(email, password) {
    try {
        email = email.trim();
        
        // Validate email domain (from auth.html)
        if (!isValidAndAllowedEmail(email)) {
            throw new Error(`Please use an approved email domain: ${ALLOWED_EMAIL_DOMAINS.join(", ")}`);
        }
        
        // Validate password length (from auth.html)
        if (password.length < 6) {
            throw new Error("Password must be at least 6 characters long");
        }
        
        // Create user in Firebase Auth
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        const user = userCredential.user;
        
        // Create user document in Firestore
        await setDoc(doc(db, "users", user.uid), {
            email: user.email,
            displayName: email.split('@')[0],
            createdAt: serverTimestamp(),
            cart: [],
            purchases: []
        });
        
        return { success: true, user: user, message: "Registration successful!" };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Login user with email and password
 */
async function loginWithEmail(email, password) {
    try {
        email = email.trim();
        
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        return { success: true, user: userCredential.user, message: "Login successful!" };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

/**
 * Login with Google (From auth.html)
 */
async function loginWithGoogle() {
    try {
        const provider = new GoogleAuthProvider();
        // Add localhost to authorized domains for development
        provider.setCustomParameters({
            prompt: 'select_account'
        });
        const result = await signInWithPopup(auth, provider);
        const user = result.user;
        
        // Create user document if it doesn't exist (non-blocking, don't fail if offline)
        // This runs in background and won't block the login
        createUserDocumentIfNeeded(user.uid, {
            email: user.email,
            displayName: user.displayName || user.email.split('@')[0],
            photoURL: user.photoURL
        }).catch(err => {
            // Silently handle offline errors - user document will be created when online
            console.log("User document creation deferred (will sync when online):", err.message);
        });
        
        return { success: true, user: user, message: "Google login successful!" };
    } catch (error) {
        if (error.code === 'auth/popup-closed-by-user') {
            return { success: false, error: "Sign-in was canceled" };
        }
        if (error.code === 'auth/unauthorized-domain') {
            return { 
                success: false, 
                error: "Localhost not authorized. Please add 'localhost' and '127.0.0.1' to Firebase Console → Authentication → Settings → Authorized domains. See GOOGLE_SIGNIN_LOCALHOST_FIX.md for details." 
            };
        }
        return { success: false, error: error.message };
    }
}

/**
 * Helper function to create user document (non-blocking, handles offline gracefully)
 */
async function createUserDocumentIfNeeded(uid, userData) {
    try {
        const userDoc = await getDoc(doc(db, "users", uid));
        if (!userDoc.exists()) {
            await setDoc(doc(db, "users", uid), {
                email: userData.email,
                displayName: userData.displayName,
                photoURL: userData.photoURL,
                createdAt: serverTimestamp(),
                cart: [],
                purchases: []
            });
            console.log("User document created successfully");
        }
    } catch (error) {
        // If offline or network error, don't throw - just log
        // Firestore will sync when connection is restored
        if (error.message.includes('offline') || error.code === 'unavailable') {
            console.log("Firestore offline - user document will be created when connection is restored");
            // Store in localStorage as backup to sync later
            const pendingUser = {
                uid: uid,
                ...userData,
                createdAt: new Date().toISOString(),
                cart: [],
                purchases: []
            };
            localStorage.setItem(`pending_user_${uid}`, JSON.stringify(pendingUser));
        } else {
            throw error; // Re-throw other errors
        }
    }
}

/**
 * Logout current user
 */
async function logout() {
    try {
        await signOut(auth);
        currentUser = null;
        notifyAuthStateChange();
        return { success: true, message: "Logged out successfully" };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// ============================================================================
// 5. AUTH STATE MANAGEMENT
// ============================================================================

/**
 * Get current logged-in user
 */
function getCurrentUser() {
    return currentUser;
}

/**
 * Check if user is logged in
 */
function isUserLoggedIn() {
    return currentUser !== null;
}

/**
 * Register callback for auth state changes
 */
function onAuthStateChange(callback) {
    authStateCallbacks.push(callback);
}

/**
 * Notify all listeners of auth state change
 */
function notifyAuthStateChange() {
    authStateCallbacks.forEach(callback => {
        try {
            callback(currentUser);
        } catch (e) {
            console.error("Error in auth state callback:", e);
        }
    });
}

/**
 * Listen to Firebase auth state changes
 */
onAuthStateChanged(auth, (user) => {
    if (user) {
        currentUser = {
            uid: user.uid,
            email: user.email,
            displayName: user.displayName,
            photoURL: user.photoURL
        };
        // Try to sync any pending user documents when user logs in
        syncPendingUserDocuments().catch(() => {});
    } else {
        currentUser = null;
    }
    notifyAuthStateChange();
});

// ============================================================================
// 6. CART MANAGEMENT (NEW - Firebase Integration)
// ============================================================================

/**
 * Save cart to Firebase for logged-in user
 */
async function saveCartToFirebase(cartItems) {
    if (!isUserLoggedIn()) {
        console.warn("User not logged in. Cart saved to localStorage instead.");
        return false;
    }
    
    try {
        // Ensure cartItems is an array
        const cartArray = Array.isArray(cartItems) ? cartItems : [];
        
        // Use setDoc with merge to ensure user document exists
        await setDoc(doc(db, "users", currentUser.uid), {
            cart: cartArray,
            lastCartUpdate: serverTimestamp()
        }, { merge: true });
        
        console.log("Cart saved to Firebase:", cartArray.length, "items");
        return true;
    } catch (error) {
        console.error("Error saving cart to Firebase:", error);
        return false;
    }
}

/**
 * Load cart from Firebase for logged-in user
 */
async function loadCartFromFirebase() {
    if (!isUserLoggedIn()) {
        console.warn("User not logged in. Cart loaded from localStorage instead.");
        return [];
    }
    
    try {
        const userDoc = await getDoc(doc(db, "users", currentUser.uid));
        if (userDoc.exists()) {
            const userData = userDoc.data();
            if (userData.cart && Array.isArray(userData.cart)) {
                console.log("Cart loaded from Firebase:", userData.cart.length, "items");
                // Also sync to localStorage
                localStorage.setItem('cart', JSON.stringify(userData.cart));
                return userData.cart;
            }
        }
        console.log("No cart found in Firebase");
        return [];
    } catch (error) {
        console.error("Error loading cart from Firebase:", error);
        return [];
    }
}

// ============================================================================
// 7. PURCHASE HISTORY MANAGEMENT (NEW)
// ============================================================================

/**
 * Save completed purchase to Firebase
 */
async function savePurchase(orderData) {
    if (!isUserLoggedIn()) {
        console.warn("User not logged in. Cannot save purchase.");
        return false;
    }
    
    try {
        const purchaseRecord = {
            items: orderData.items || [],
            amount: orderData.amount || 0,
            paymentMethod: orderData.paymentMethod || "card",
            purchaseDate: serverTimestamp(),
            status: "completed",
            orderId: `ORD${Date.now()}${Math.random().toString(36).substr(2, 9)}`.toUpperCase()
        };
        
        // Add to purchases subcollection
        await addDoc(
            collection(db, "users", currentUser.uid, "purchases"),
            purchaseRecord
        );
        
        // Clear cart after purchase
        await saveCartToFirebase([]);
        
        return purchaseRecord;
    } catch (error) {
        console.error("Error saving purchase:", error);
        return false;
    }
}

/**
 * Get purchase history for logged-in user
 */
async function getPurchaseHistory() {
    if (!isUserLoggedIn()) {
        return [];
    }
    
    try {
        const purchasesQuery = query(
            collection(db, "users", currentUser.uid, "purchases")
        );
        const querySnapshot = await getDocs(purchasesQuery);
        
        const purchases = [];
        querySnapshot.forEach((doc) => {
            purchases.push({
                id: doc.id,
                ...doc.data(),
                purchaseDate: doc.data().purchaseDate?.toDate?.() || new Date()
            });
        });
        
        return purchases.sort((a, b) => b.purchaseDate - a.purchaseDate);
    } catch (error) {
        console.error("Error loading purchase history:", error);
        return [];
    }
}

/**
 * Track previously bought items (for "Add to Cart" feature)
 */
async function addToPreviousBought(itemPath) {
    if (!isUserLoggedIn()) return false;
    
    try {
        const userDocRef = doc(db, "users", currentUser.uid);
        const userDoc = await getDoc(userDocRef);
        
        let previouslyBought = userDoc.data()?.previouslyBought || [];
        if (!previouslyBought.includes(itemPath)) {
            previouslyBought.push(itemPath);
            await updateDoc(userDocRef, { previouslyBought });
        }
        
        return true;
    } catch (error) {
        console.error("Error updating previously bought items:", error);
        return false;
    }
}

/**
 * Get all previously bought items
 */
async function getPreviouslyBought() {
    if (!isUserLoggedIn()) return [];
    
    try {
        const userDoc = await getDoc(doc(db, "users", currentUser.uid));
        return userDoc.data()?.previouslyBought || [];
    } catch (error) {
        console.error("Error loading previously bought items:", error);
        return [];
    }
}

// ============================================================================
// 8. MODAL FUNCTIONS
// ============================================================================

/**
 * Open authentication modal
 */
function openAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

/**
 * Close authentication modal
 */
function closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ============================================================================
// 9. EXPORT ALL FUNCTIONS
// ============================================================================
export {
    // Auth Functions
    registerWithEmail,
    loginWithEmail,
    loginWithGoogle,
    logout,
    
    // Auth State
    getCurrentUser,
    isUserLoggedIn,
    onAuthStateChange,
    
    // Cart Functions
    saveCartToFirebase,
    loadCartFromFirebase,
    
    // Purchase Functions
    savePurchase,
    getPurchaseHistory,
    addToPreviousBought,
    getPreviouslyBought,
    
    // Modal Functions
    openAuthModal,
    closeAuthModal
};
