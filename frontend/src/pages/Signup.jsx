
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Sparkles,
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  ShoppingBag,
} from "lucide-react";

function Signup() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (password !== confirmPassword) {
      setError("Passwords do not match!");
      return;
    }

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:5000/api/auth/register",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: name.trim(),
            email: email.trim(),
            password: password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Registration failed.");
      }

      setSuccess("Registration successful! Redirecting to Login...");

      setTimeout(() => {
        navigate("/login");
      }, 1500);

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
            <ShoppingBag size={30} />
          </div>

          <h1 className="text-5xl font-bold leading-tight">
            Join the future
            <br />
            of shopping.
          </h1>

          <p className="text-purple-100 text-lg mt-6 leading-8">
            Create your account and explore intelligent
            recommendations, AI review insights and
            smarter product comparisons.
          </p>

          <div className="mt-10 flex gap-4 items-center">
            <div className="bg-white/15 p-3 rounded-xl">
              <Sparkles size={23} />
            </div>
            <div>
              <p className="font-semibold">Your personal shopping assistant</p>
              <p className="text-purple-200 text-sm">
                Discover products that match you.
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

          <Link to="/" className="lg:hidden flex items-center gap-2 mb-10">
            <div className="bg-purple-600 text-white p-2 rounded-xl">
              <Sparkles size={22} />
            </div>
            <span className="text-xl font-bold">
              ShopSense <span className="text-purple-600">AI</span>
            </span>
          </Link>

          <div className="mb-8">
            <p className="text-purple-600 font-semibold text-sm">
              GET STARTED
            </p>

            <h2 className="text-3xl font-bold mt-3">
              Create your account
            </h2>

            <p className="text-gray-500 mt-3">
              Join ShopSense AI and shop smarter.
            </p>
          </div>

          <form onSubmit={handleSignup} className="space-y-5">

            {/* Name */}
            <div>
              <label className="block text-sm font-semibold mb-2">
                Full Name
              </label>

              <div className="relative">
                <User
                  size={19}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                />

                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full border border-gray-200 rounded-xl pl-12 pr-4 py-3.5 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-100"
                />
              </div>
            </div>

            {/* Email */}
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

            {/* Password */}
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
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a password"
                  className="w-full border border-gray-200 rounded-xl pl-12 pr-12 py-3.5 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-100"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400"
                >
                  {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-semibold mb-2">
                Confirm Password
              </label>

              <div className="relative">
                <Lock
                  size={19}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                />

                <input
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  className="w-full border border-gray-200 rounded-xl pl-12 pr-12 py-3.5 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-100"
                />

                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400"
                >
                  {showConfirmPassword ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
            </div>

            {error && (
              <p className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">
                {error}
              </p>
            )}

            {success && (
              <p className="text-green-700 text-sm bg-green-50 p-3 rounded-lg">
                {success}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-60 text-white py-3.5 rounded-xl font-semibold flex justify-center items-center gap-2 transition"
            >
              {loading ? "Creating Account..." : "Create Account"}
              {!loading && <ArrowRight size={19} />}
            </button>

          </form>

          <div className="text-center mt-7 text-sm text-gray-500">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-purple-600 font-bold hover:underline"
            >
              Login
            </Link>
          </div>

          <div className="mt-8 text-center">
            <Link to="/" className="text-sm text-gray-400 hover:text-purple-600">
              ← Back to Home
            </Link>
          </div>

        </div>
      </div>
    </div>
  );
}

export default Signup;
