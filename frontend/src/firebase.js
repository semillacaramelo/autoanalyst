import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getFunctions } from "firebase/functions";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDRCi3__4i5ac4stvXmkpLDfVkYHU_jTHU",
  authDomain: "autoanalyst-10589.firebaseapp.com",
  projectId: "autoanalyst-10589",
  storageBucket: "autoanalyst-10589.firebasestorage.app",
  messagingSenderId: "931078230882",
  appId: "1:931078230882:web:8354b6c7d6787e4d9b123b",
  measurementId: "G-HWLL67S28D"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);


// Export Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);
export const functions = getFunctions(app);
export const googleProvider = new GoogleAuthProvider();