import { GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signOut } from "firebase/auth";
import { create } from "zustand";

import { firebaseAuth } from "../../../shared/lib/firebase";

type AuthStatus = "loading" | "signedOut" | "signedIn";

interface AuthState {
  status: AuthStatus;
  email: string | null;
  error: string | null;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  status: "loading",
  email: null,
  error: null,
  signIn: async () => {
    try {
      set({ error: null });
      await signInWithPopup(firebaseAuth, new GoogleAuthProvider());
    } catch (error) {
      set({ error: error instanceof Error ? error.message : String(error) });
    }
  },
  signOut: async () => {
    await signOut(firebaseAuth);
  },
}));

onAuthStateChanged(firebaseAuth, (user) => {
  useAuthStore.setState({
    status: user ? "signedIn" : "signedOut",
    email: user?.email ?? null,
  });
});
