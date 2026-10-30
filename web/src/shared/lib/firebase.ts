import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

import { CONFIG } from "./config";

export const firebaseApp = initializeApp(CONFIG.firebase);
export const firebaseAuth = getAuth(firebaseApp);
