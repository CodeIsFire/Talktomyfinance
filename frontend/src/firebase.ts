import { initializeApp } from 'firebase/app';
import { getAnalytics } from 'firebase/analytics';

const firebaseConfig = {
  apiKey: 'AIzaSyDKwM_OnCW_jAeWLQIuVjvRZYZYFPMI-pQ',
  authDomain: 'talkwithfinance.firebaseapp.com',
  projectId: 'talkwithfinance',
  storageBucket: 'talkwithfinance.firebasestorage.app',
  messagingSenderId: '1017113501341',
  appId: '1:1017113501341:web:e29306fd4200b9f3e1be74',
  measurementId: 'G-6SKD49K33L',
};

const app = initializeApp(firebaseConfig);
getAnalytics(app);

export default app;
