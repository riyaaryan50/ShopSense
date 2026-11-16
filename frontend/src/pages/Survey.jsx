import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ClipboardList,
  Heart,
  Package,
  RotateCcw,
  ShoppingCart,
  Sparkles,
} from "lucide-react";

import Navbar from "../components/Navbar";
import { useCart } from "../context/CartContext";
import { API_URL, formatPrice, getToken } from "../config";
import {
  getSavedSurvey,
  getSurveyRecommendations,
  saveSurvey,
  storeGuestSurvey,
} from "../services/aiService";
import ProductImage from "../components/ProductImage";

const ROLES = [
  { value: "school", label: "School student" },
  { value: "undergrad", label: "College undergraduate" },
  { value: "postgrad", label: "Postgraduate" },
  { value: "professional", label: "Working professional" },
  { value: "other", label: "Something else" },
];

const USES = [
  { value: "online_classes", label: "Online classes & calls" },
  { value: "coding", label: "Coding & programming" },
  { value: "note_taking", label: "Note-taking & PDFs" },
  { value: "music", label: "Music & audio" },
  { value: "hostel_living", label: "Hostel living" },
  { value: "travel", label: "Travel & commute" },
  { value: "printing", label: "Printing assignments" },
  { value: "exam_prep", label: "Exam prep (maths/science)" },
  { value: "entertainment", label: "Videos & entertainment" },
  { value: "photography", label: "Photos & scanning" },
];

const PRIORITIES = [
  { value: "price", label: "Low price" },
  { value: "performance", label: "Performance" },
  { value: "battery", label: "Battery life" },
  { value: "portability", label: "Portability" },
  { value: "durability", label: "Durability" },
  { value: "comfort", label: "Comfort" },
  { value: "display", label: "Display" },
  { value: "brand", label: "Trusted brand" },
];

const BUDGETS = [1000, 3000, 10000, 25000, 65000];

const STEPS = ["About you", "Interests", "Usage", "Budget", "Priorities"];

const EMPTY = {
  role: "",
  interests: [],
  uses: [],
  budget_max: "",
  priorities: [],
  brands: [],
  description: "",
};

function Chip({ selected, onClick, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`flex items-center gap-2 rounded-xl border px-4 py-3 text-left text-sm font-medium transition ${
        selected
          ? "border-purple-600 bg-purple-600 text-white"
          : "border-gray-200 bg-white text-gray-700 hover:border-purple-300"
      }`}
    >
      {selected && <Check size={16} />}
      {children}
    </button>
  );
}

function Survey() {
  const { addToCart, toggleWishlist, wishlist } = useCart();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState(EMPTY);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const loggedIn = Boolean(getToken());

  // Catalogue categories + brands for the options, and any saved survey.
  useEffect(() => {
    (async () => {
      try {
        const response = await fetch(`${API_URL}/products/`);
        const products = await response.json();
        setCategories([...new Set(products.map((p) => p.category).filter(Boolean))].sort());
        setBrands([...new Set(products.map((p) => p.brand).filter(Boolean))].sort());
      } catch {
        setError("Could not load the catalogue. Is the backend running?");
      }

      try {
        const saved = await getSavedSurvey();
        if (saved) {
          setAnswers({ ...EMPTY, ...saved });
          const data = await getSurveyRecommendations(saved);
          setResults(data);
        }
      } catch {
        /* no saved survey – start fresh */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const toggle = (key, value, max) =>
    setAnswers((prev) => {
      const list = prev[key];
      if (list.includes(value)) return { ...prev, [key]: list.filter((v) => v !== value) };
      if (max && list.length >= max) return prev;
      return { ...prev, [key]: [...list, value] };
    });

  const canContinue = useMemo(() => {
    if (step === 0) return Boolean(answers.role);
    if (step === 1) return answers.interests.length > 0;
    if (step === 2) return answers.uses.length > 0;
    return true;
  }, [step, answers]);

  const submit = async () => {
    setSubmitting(true);
    setError("");
    const payload = {
      ...answers,
      budget_max: answers.budget_max === "" ? null : Number(answers.budget_max),
    };
    try {
      if (loggedIn) {
        await saveSurvey(payload);
      } else {
        storeGuestSurvey(payload);
      }
      const data = await getSurveyRecommendations(payload);
      setResults(data);
      window.dispatchEvent(new Event("recommendations-updated"));
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const restart = () => {
    setResults(null);
    setStep(0);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f8f8fc]">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-purple-200 border-t-purple-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8f8fc] text-gray-900">
      <Navbar searchQuery="" setSearchQuery={() => {}} />

      <main className="mx-auto max-w-5xl px-4 py-10 md:px-8">
        <Link to="/" className="mb-6 inline-flex items-center gap-2 text-gray-500 hover:text-purple-600">
          <ArrowLeft size={18} /> Back to shopping
        </Link>

        {error && (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
        )}

        {results ? (
          <Results
            results={results}
            loggedIn={loggedIn}
            onRestart={restart}
            addToCart={addToCart}
            toggleWishlist={toggleWishlist}
            wishlist={wishlist}
          />
        ) : (
          <section className="rounded-3xl bg-white p-6 shadow-sm md:p-10">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-purple-100 p-3 text-purple-600">
                <ClipboardList size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-bold md:text-3xl">Tell us what you need</h1>
                <p className="text-sm text-gray-500">
                  1-minute survey · we'll match products to your answers with AI
                </p>
              </div>
            </div>

            {/* Progress */}
            <ol className="mt-8 flex gap-2" aria-label="Survey progress">
              {STEPS.map((label, i) => (
                <li key={label} className="flex-1">
                  <div className={`h-2 rounded-full ${i <= step ? "bg-purple-600" : "bg-gray-200"}`} />
                  <p className={`mt-2 hidden text-xs sm:block ${i === step ? "font-semibold text-purple-700" : "text-gray-400"}`}>
                    {label}
                  </p>
                </li>
              ))}
            </ol>

            <div className="mt-8 min-h-[260px]">
              {step === 0 && (
                <Question title="Which best describes you?">
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {ROLES.map((r) => (
                      <Chip
                        key={r.value}
                        selected={answers.role === r.value}
                        onClick={() => setAnswers((a) => ({ ...a, role: r.value }))}
                      >
                        {r.label}
                      </Chip>
                    ))}
                  </div>
                </Question>
              )}

              {step === 1 && (
                <Question title="What are you shopping for?" hint="Pick all that apply">
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {categories.map((c) => (
                      <Chip key={c} selected={answers.interests.includes(c)} onClick={() => toggle("interests", c)}>
                        {c}
                      </Chip>
                    ))}
                  </div>
                </Question>
              )}

              {step === 2 && (
                <Question title="How will you use it?" hint="Pick all that apply">
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {USES.map((u) => (
                      <Chip key={u.value} selected={answers.uses.includes(u.value)} onClick={() => toggle("uses", u.value)}>
                        {u.label}
                      </Chip>
                    ))}
                  </div>
                </Question>
              )}

              {step === 3 && (
                <Question title="What's your budget per item?">
                  <div className="grid gap-3 sm:grid-cols-3">
                    {BUDGETS.map((b) => (
                      <Chip
                        key={b}
                        selected={Number(answers.budget_max) === b}
                        onClick={() => setAnswers((a) => ({ ...a, budget_max: b }))}
                      >
                        Up to {formatPrice(b)}
                      </Chip>
                    ))}
                    <Chip
                      selected={answers.budget_max === ""}
                      onClick={() => setAnswers((a) => ({ ...a, budget_max: "" }))}
                    >
                      No fixed budget
                    </Chip>
                  </div>
                  <label className="mt-5 block text-sm text-gray-600">
                    Or enter an amount (₹)
                    <input
                      type="number"
                      min="0"
                      value={answers.budget_max}
                      onChange={(e) => setAnswers((a) => ({ ...a, budget_max: e.target.value }))}
                      className="mt-2 block w-full max-w-xs rounded-xl border border-gray-200 px-4 py-3 outline-none focus:border-purple-500"
                      placeholder="e.g. 5000"
                    />
                  </label>
                </Question>
              )}

              {step === 4 && (
                <div className="space-y-8">
                  <Question title="What matters most?" hint="Choose up to 3">
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                      {PRIORITIES.map((p) => (
                        <Chip
                          key={p.value}
                          selected={answers.priorities.includes(p.value)}
                          onClick={() => toggle("priorities", p.value, 3)}
                        >
                          {p.label}
                        </Chip>
                      ))}
                    </div>
                  </Question>

                  <Question title="Any preferred brands?" hint="Optional">
                    <div className="flex flex-wrap gap-2">
                      {brands.map((b) => (
                        <button
                          key={b}
                          type="button"
                          aria-pressed={answers.brands.includes(b)}
                          onClick={() => toggle("brands", b)}
                          className={`rounded-full border px-4 py-1.5 text-sm ${
                            answers.brands.includes(b)
                              ? "border-purple-600 bg-purple-600 text-white"
                              : "border-gray-200 text-gray-600 hover:border-purple-300"
                          }`}
                        >
                          {b}
                        </button>
                      ))}
                    </div>
                  </Question>

                  <Question title="Describe what you're looking for" hint="Optional – our AI reads this">
                    <textarea
                      value={answers.description}
                      onChange={(e) => setAnswers((a) => ({ ...a, description: e.target.value }))}
                      rows={3}
                      maxLength={500}
                      placeholder="e.g. Something light for taking notes in lectures that lasts all day"
                      className="w-full rounded-xl border border-gray-200 p-4 text-sm outline-none focus:border-purple-500"
                    />
                  </Question>
                </div>
              )}
            </div>

            <div className="mt-8 flex items-center justify-between gap-4 border-t pt-6">
              <button
                type="button"
                onClick={() => setStep((s) => Math.max(0, s - 1))}
                disabled={step === 0}
                className="flex items-center gap-2 rounded-xl px-5 py-3 font-semibold text-gray-600 hover:bg-gray-100 disabled:opacity-30"
              >
                <ArrowLeft size={18} /> Back
              </button>

              {step < STEPS.length - 1 ? (
                <button
                  type="button"
                  onClick={() => setStep((s) => s + 1)}
                  disabled={!canContinue}
                  className="flex items-center gap-2 rounded-xl bg-purple-600 px-6 py-3 font-semibold text-white hover:bg-purple-700 disabled:bg-gray-300"
                >
                  Next <ArrowRight size={18} />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={submit}
                  disabled={submitting}
                  className="flex items-center gap-2 rounded-xl bg-purple-600 px-6 py-3 font-semibold text-white hover:bg-purple-700 disabled:bg-gray-300"
                >
                  <Sparkles size={18} />
                  {submitting ? "Finding matches…" : "Show my recommendations"}
                </button>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function Question({ title, hint, children }) {
  return (
    <fieldset>
      <legend className="text-lg font-bold">{title}</legend>
      {hint && <p className="mb-4 mt-1 text-sm text-gray-500">{hint}</p>}
      {!hint && <div className="mb-4" />}
      {children}
    </fieldset>
  );
}

function Results({ results, loggedIn, onRestart, addToCart, toggleWishlist, wishlist }) {
  const items = results.recommendations || [];
  return (
    <section>
      <div className="rounded-3xl bg-gradient-to-r from-purple-700 to-indigo-600 p-6 text-white md:p-8">
        <p className="flex items-center gap-2 text-sm font-semibold text-purple-200">
          <Sparkles size={16} /> YOUR SURVEY MATCHES
        </p>
        <h1 className="mt-2 text-2xl font-bold md:text-3xl">Products picked from your answers</h1>
        <p className="mt-2 max-w-2xl text-sm text-purple-100">
          Ranked by semantic match to your needs (MiniLM embeddings), category, budget, brand
          and customer review sentiment.
          {loggedIn
            ? " Your answers are saved and also shape the “Recommended For You” section."
            : " Log in to save your answers to your account."}
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <button
            onClick={onRestart}
            className="flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2 text-sm font-semibold hover:bg-white/25"
          >
            <RotateCcw size={16} /> Retake survey
          </button>
          <Link to="/" className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-purple-700">
            Continue shopping
          </Link>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="mt-8 rounded-2xl bg-white p-10 text-center text-gray-500">
          No matching products. Try widening your budget or interests.
        </div>
      ) : (
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((product, index) => {
            const wished = wishlist.some((w) => Number(w.id) === Number(product.id));
            return (
              <article key={product.id} className="flex flex-col overflow-hidden rounded-2xl border border-gray-100 bg-white">
                <Link to={`/product/${product.id}`} className="relative block h-44 bg-gray-50">
                  {product.image_url ? (
                    <ProductImage src={product.image_url} alt={product.name} className="h-44 w-full object-contain p-4" />
                  ) : (
                    <div className="flex h-44 items-center justify-center text-purple-300">
                      <Package size={44} />
                    </div>
                  )}
                  <span className="absolute left-3 top-3 rounded-full bg-purple-600 px-3 py-1 text-xs font-bold text-white">
                    #{index + 1} · {Math.round(product.match_score)}% match
                  </span>
                </Link>
                <div className="flex flex-1 flex-col p-5">
                  <p className="text-xs font-semibold uppercase text-purple-600">{product.category}</p>
                  <Link to={`/product/${product.id}`} className="mt-1 font-bold hover:text-purple-600">
                    {product.name}
                  </Link>
                  <ul className="mt-3 flex-1 space-y-1.5 text-sm text-gray-600">
                    {(product.reasons || []).map((reason) => (
                      <li key={reason} className="flex gap-2">
                        <Check size={16} className="mt-0.5 shrink-0 text-green-600" />
                        {reason}
                      </li>
                    ))}
                  </ul>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-lg font-bold">{formatPrice(product.price)}</span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => toggleWishlist(product)}
                        aria-label="Toggle wishlist"
                        className="rounded-xl border border-gray-200 p-2.5 hover:border-purple-300"
                      >
                        <Heart size={18} className={wished ? "fill-red-500 text-red-500" : "text-gray-600"} />
                      </button>
                      <button
                        onClick={() => addToCart(product)}
                        aria-label="Add to cart"
                        className="rounded-xl bg-purple-600 p-2.5 text-white hover:bg-purple-700"
                      >
                        <ShoppingCart size={18} />
                      </button>
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default Survey;
