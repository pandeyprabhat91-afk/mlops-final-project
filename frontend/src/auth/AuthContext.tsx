import { createContext, useContext, useState, type ReactNode } from "react";

export type Role = "user" | "admin";

export interface RegisteredUser {
  username: string;
  passwordHash: string; // plain text for this academic project — no real auth
  name: string;
  email: string;
  role: Role;
}

interface AuthState {
  role: Role | null;
  username: string;
  login: (username: string, password: string) => boolean;
  loginAsDemo: () => void;
  logout: () => void;
  register: (name: string, email: string, username: string, password: string) => { ok: boolean; error?: string };
  getUsers: () => RegisteredUser[];
}

const HARDCODED: Record<string, { password: string; role: Role }> = {
  admin: { password: "admin123", role: "admin" },
  user:  { password: "user123",  role: "user"  },
};

const STORAGE_KEY = "ds_users";

function loadUsers(): RegisteredUser[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function saveUsers(users: RegisteredUser[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(users));
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role | null>(null);
  const [username, setUsername] = useState("");

  const login = (u: string, p: string): boolean => {
    const key = u.toLowerCase();
    // Check hardcoded first
    const hard = HARDCODED[key];
    if (hard && hard.password === p) {
      setRole(hard.role);
      setUsername(u);
      return true;
    }
    // Check localStorage users
    const stored = loadUsers().find(usr => usr.username.toLowerCase() === key && usr.passwordHash === p);
    if (stored) {
      setRole(stored.role);
      setUsername(stored.username);
      return true;
    }
    return false;
  };

  const register = (name: string, email: string, uname: string, password: string): { ok: boolean; error?: string } => {
    const key = uname.toLowerCase();
    if (HARDCODED[key]) return { ok: false, error: "Username already taken." };
    const users = loadUsers();
    if (users.find(u => u.username.toLowerCase() === key)) return { ok: false, error: "Username already taken." };
    if (users.find(u => u.email.toLowerCase() === email.toLowerCase())) return { ok: false, error: "Email already registered." };
    const newUser: RegisteredUser = { username: uname, passwordHash: password, name, email, role: "user" };
    saveUsers([...users, newUser]);
    setRole("user");
    setUsername(uname);
    return { ok: true };
  };

  const getUsers = (): RegisteredUser[] => loadUsers();

  const loginAsDemo = () => { setRole("user"); setUsername("demo"); };

  const logout = () => {
    setRole(null);
    setUsername("");
    document.documentElement.removeAttribute("data-theme");
    localStorage.setItem("theme", "dark");
    window.location.hash = "";
    window.scrollTo(0, 0);
  };

  return (
    <AuthContext.Provider value={{ role, username, login, loginAsDemo, logout, register, getUsers }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
