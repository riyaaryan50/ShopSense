
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Sparkles,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  ShoppingBag,
} from "lucide-react";

function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:5000/api/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email.trim(),
            password: password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Login failed. Please try again.");
      }

      // Store JWT and user details
      const storage = rememberMe ? localStorage : sessionStorage;

      storage.setItem("access_token", data.access_token);
      storage.setItem("user", JSON.stringify(data.user));

      alert("Login successful!");

      navigate("/");
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot connect to the server. Please check if the backend is running."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-white">

      {/* Left Side */}
      <div className="hidden lg:flex flex-col justify-between bg-gradient-to-br from-purple-700 via-purple-600 to-indigo-700 text-white p-12 relative overflow-hidden">

        <div className="absolute w-96 h-96 bg-white/10 rounded-full -top-32 -right-32" />
        <div className="absolute w-80 h-80 bg-white/10 rounded-full -bottom-20 -left-20" />

        <Link to="/" className="relative flex items-center gap-3">
          <div className="bg-white/20 p-3 rounded-xl">
            <Sparkles size={27} />
          </div>
          <span className="text-2xl font-bold">ShopSense AI</span>
        </Link>

        <div className="relative max-w-lg">
          <div className="bg-white/15 backdrop-blur rounded-2xl p-4 inline-flex mb-7">
            <Sparkles size={30} />
          </div>

          <h1 className="text-5xl font-bold leading-tight">
            Discover smarter.
            <br />
            Shop better.
          </h1>

          <p className="text-purple-100 text-lg mt-6 leading-8">
            Your intelligent shopping companion.
            Discover personalized products, compare prices
            and understand customer reviews with AI.
          </p>

          <div className="mt-10 flex gap-4 items-center">
            <div className="bg-white/15 p-3 rounded-xl">
              <ShoppingBag size={23} />
            </div>
            <div>
              <p className="font-semibold">A smarter way to shop</p>
              <p className="text-purple-200 text-sm">
                Everything you need in one place.
              </p>
            </div>
          </div>
        </div>

        <p className="relative text-sm text-purple-200">
          © 2026 ShopSense AI. All rights reserved.
        </p>
      </div>

      {/* Right Side */}
      <div className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">

          <Link to="/" className="lg:hidden flex items-center gap-2 mb-12">
            <div className="bg-purple-600 text-white p-2 rounded-xl">
              <Sparkles size={22} />
            </div>
            <span className="text-xl font-bold">
              ShopSense <span className="text-purple-600">AI</span>
            </span>
          </Link>

          <div className="mb-9">
            <p className="text-purple-600 font-semibold text-sm">
              WELCOME BACK
            </p>

            <h2 className="text-3xl font-bold mt-3">
              Login to your account
            </h2>

            <p className="text-gray-500 mt-3">
              Welcome back! Please enter your details.
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">

            <div>
              <label className="block text-sm font-semibold mb-2">
                Email Address
              </label>

              <div className="relative">
                <Mail
                  size={19}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                />

                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="w-full border border-gray-200 rounded-xl pl-12 pr-4 py-3.5 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-100"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">
                Password
              </label>

              <div className="relative">
                <Lock
                  size={19}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                />

                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full border border-gray-200 rounded-xl pl-12 pr-12 py-3.5 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-100"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400"
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
            </div>

            <div className="flex justify-between items-center text-sm">
              <label className="flex items-center gap-2 text-gray-600">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="accent-purple-600"
                />
                Remember me
              </label>

              <button
                type="button"
                onClick={() => alert("Password recovery will be added soon.")}
                className="text-purple-600 font-semibold"
              >
                Forgot password?
              </button>
            </div>

            {error && (
              <p className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-60 text-white py-3.5 rounded-xl font-semibold flex justify-center items-center gap-2 transition"
            >
              {loading ? "Logging in..." : "Login"}
              {!loading && <ArrowRight size={19} />}
            </button>

          </form>

          <div className="text-center mt-8 text-sm text-gray-500">
            Don't have an account?{" "}
            <Link
              to="/signup"
              className="text-purple-600 font-bold hover:underline"
            >
              Create account
            </Link>
          </div>

          <div className="mt-10 text-center">
            <Link to="/" className="text-sm text-gray-400 hover:text-purple-600">
              ← Back to Home
            </Link>
          </div>

        </div>
      </div>
    </div>
  );
}

export default Login;
