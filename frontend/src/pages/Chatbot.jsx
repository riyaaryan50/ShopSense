
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Bot,
  Send,
  Sparkles,
  User,
  ShoppingBag,
  Headphones,
  Shirt,
  Laptop,
} from "lucide-react";

function Chatbot() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hi! I'm ShopSense AI Assistant. ✨ How can I help you today? You can ask me about products, recommendations, or shopping deals.",
    },
  ]);

  const quickQuestions = [
    "Recommend a product for me",
    "Suggest wireless headphones",
    "What are the trending products?",
    "Help me choose a gift",
  ];

  const getBotResponse = (question) => {
    const text = question.toLowerCase();

    if (text.includes("headphone")) {
      return "Wireless Headphones are a great choice! 🎧 You can explore our Wireless Headphones priced at ₹2,499. Visit the product page to learn more.";
    }

    if (text.includes("gift")) {
      return "I'd be happy to help you choose a gift! 🎁 Consider a Smart Watch, Bluetooth Speaker, or Classic Sunglasses depending on the recipient's interests.";
    }

    if (text.includes("trending")) {
      return "Some popular picks in our demo store include Smart Watches, Wireless Headphones, Running Shoes, and Bluetooth Speakers. Explore our homepage to see them!";
    }

    if (text.includes("recommend") || text.includes("suggest")) {
      return "Sure! ✨ I can help you discover products. Tell me what category you're interested in, your budget, or what you need the product for.";
    }

    return "That's a great question! 😊 I'm currently running in demo mode. You can ask me about headphones, gifts, trending products, or recommendations.";
  };

  const sendMessage = (text = message) => {
    const trimmedMessage = text.trim();

    if (!trimmedMessage) return;

    setMessages((previous) => [
      ...previous,
      { sender: "user", text: trimmedMessage },
    ]);

    setMessage("");

    setTimeout(() => {
      setMessages((previous) => [
        ...previous,
        {
          sender: "bot",
          text: getBotResponse(trimmedMessage),
        },
      ]);
    }, 500);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-white to-purple-100 px-4 py-8">
      <div className="mx-auto max-w-5xl">

        <Link
          to="/"
          className="mb-6 inline-flex items-center gap-2 font-semibold text-violet-700 hover:text-violet-900"
        >
          <ArrowLeft size={19} />
          Back to Shopping
        </Link>

        <div className="overflow-hidden rounded-3xl border border-violet-100 bg-white shadow-xl">

          {/* Header */}
          <div className="flex items-center gap-4 bg-gradient-to-r from-violet-700 to-purple-600 p-6 text-white">
            <div className="rounded-2xl bg-white/20 p-3">
              <Bot size={30} />
            </div>

            <div className="flex-1">
              <h1 className="text-2xl font-bold">
                ShopSense AI Assistant
              </h1>
              <p className="mt-1 text-sm text-violet-100">
                Your personal shopping companion
              </p>
            </div>

            <div className="hidden items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-sm sm:flex">
              <span className="h-2 w-2 rounded-full bg-green-300"></span>
              Online
            </div>
          </div>

          {/* Chat area */}
          <div className="min-h-[420px] space-y-5 bg-slate-50 p-5 sm:p-8">

            {messages.map((item, index) => (
              <div
                key={index}
                className={`flex gap-3 ${
                  item.sender === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                {item.sender === "bot" && (
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-violet-100 text-violet-700">
                    <Bot size={21} />
                  </div>
                )}

                <div
                  className={`max-w-[80%] rounded-2xl px-5 py-3 text-sm leading-7 shadow-sm ${
                    item.sender === "user"
                      ? "rounded-br-sm bg-violet-700 text-white"
                      : "rounded-bl-sm border border-violet-100 bg-white text-gray-700"
                  }`}
                >
                  {item.text}
                </div>

                {item.sender === "user" && (
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-purple-200 text-purple-800">
                    <User size={20} />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Quick questions */}
          <div className="border-t border-gray-100 bg-white px-5 py-5">
            <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-600">
              <Sparkles size={16} className="text-violet-600" />
              Try asking
            </p>

            <div className="flex flex-wrap gap-2">
              {quickQuestions.map((question) => (
                <button
                  key={question}
                  onClick={() => sendMessage(question)}
                  className="rounded-full border border-violet-200 px-4 py-2 text-xs font-medium text-violet-700 transition hover:bg-violet-50"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>

          {/* Message input */}
          <div className="border-t border-gray-100 bg-white p-5">
            <form
              onSubmit={(event) => {
                event.preventDefault();
                sendMessage();
              }}
              className="flex items-center gap-3 rounded-2xl border border-violet-200 bg-gray-50 p-2 focus-within:border-violet-500"
            >
              <input
                type="text"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Ask me anything about shopping..."
                className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm outline-none"
              />

              <button
                type="submit"
                disabled={!message.trim()}
                className="rounded-xl bg-violet-700 p-3 text-white transition hover:bg-violet-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send size={19} />
              </button>
            </form>

            <p className="mt-3 text-center text-xs text-gray-400">
              Demo assistant · AI backend integration will be connected later
            </p>
          </div>
        </div>

        {/* Feature cards */}
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-violet-100 bg-white p-5">
            <ShoppingBag className="mb-3 text-violet-600" />
            <h3 className="font-bold text-gray-800">Product Discovery</h3>
            <p className="mt-1 text-sm text-gray-500">
              Find products based on your needs.
            </p>
          </div>

          <div className="rounded-2xl border border-violet-100 bg-white p-5">
            <Headphones className="mb-3 text-violet-600" />
            <h3 className="font-bold text-gray-800">Smart Suggestions</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get help choosing the right products.
            </p>
          </div>

          <div className="rounded-2xl border border-violet-100 bg-white p-5">
            <Laptop className="mb-3 text-violet-600" />
            <h3 className="font-bold text-gray-800">Shopping Assistance</h3>
            <p className="mt-1 text-sm text-gray-500">
              Explore products with conversational help.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}

export default Chatbot;
