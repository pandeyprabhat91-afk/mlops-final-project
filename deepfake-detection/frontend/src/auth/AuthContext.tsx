import { createContext, useContext, useState, type ReactNode } from "react";

export type Role = "user" | "admin";

interface AuthState {
  role: Role | null;
  username: string;
  login: (username: string, password: string) => boolean;
  logout: () => void;
}

const CREDENTIALS: Record<string, { password: string; role: Role }> = {
  admin: { password: "admin123", role: "admin" },
  user:  { password: "user123",  role: "user"  },
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role | null>(null);
  const [username, setUsername] = useState("");

  const login = (u: string, p: string): boolean => {
    const cred = CREDENTIALS[u.toLowerCase()];
    if (cred && cred.password === p) {
      setRole(cred.role);
      setUsername(u);
      return true;
    }
    return false;
  };

  const logout = () => { setRole(null); setUsername(""); };

  return (
    <AuthContext.Provider value={{ role, username, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
