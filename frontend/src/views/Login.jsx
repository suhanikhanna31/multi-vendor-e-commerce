import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Login failed");
      }

      sessionStorage.setItem("access_token", data.access_token);
      sessionStorage.setItem("role", data.role);

      // vendor_id is embedded in the JWT claims, not the top-level response —
      // decode the token payload to pull it out for vendor-scoped API calls
      try {
        const payload = JSON.parse(atob(data.access_token.split(".")[1]));
        if (payload.vendor_id) {
          sessionStorage.setItem("vendor_id", payload.vendor_id);
        }
      } catch {
        // token wasn't a standard JWT shape — vendor-scoped routes just
        // won't have a vendor_id available, non-fatal for admin/analyst roles
      }

      if (data.role === "admin") navigate("/admin");
      else if (data.role === "vendor") navigate("/vendor/orders");
      else if (data.role === "analyst") navigate("/analyst/reports");
      else navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "360px", margin: "4rem auto", padding: "2rem" }}>
      <h1>Log In</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </div>
        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </div>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ width: "100%", padding: "0.6rem" }}>
          {loading ? "Logging in..." : "Log In"}
        </button>
      </form>
    </div>
  );
}
