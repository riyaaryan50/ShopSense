import { Link } from "react-router-dom";
import { ArrowLeft, Bot, GitCompare, MessageSquareText, Search, Sparkles } from "lucide-react";

import ChatPanel from "../components/chat/ChatPanel";

const FEATURES = [
  { icon: Search, title: "Semantic search", text: "“Something to keep tea hot in class” finds the thermos – no exact keywords needed." },
  { icon: Sparkles, title: "Recommendations", text: "Personal picks from your history and survey, or suggestions ranked by review sentiment." },
  { icon: GitCompare, title: "Compare products", text: "Side-by-side price, specs, ratings and what customers like or dislike." },
  { icon: MessageSquareText, title: "Review insights", text: "VADER sentiment over every review, with the top praised and complained-about themes." },
];

function Chatbot() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 via-white to-brand-100 px-4 py-8">
      <div className="mx-auto max-w-5xl">
        <Link
          to="/"
          className="mb-6 inline-flex items-center gap-2 font-semibold text-brand-700 hover:text-brand-900"
        >
          <ArrowLeft size={19} />
          Back to Shopping
        </Link>

        <div className="overflow-hidden rounded-3xl border border-brand-100 bg-white shadow-xl">
          <div className="flex items-center gap-4 bg-gradient-to-r from-brand-700 to-brand-600 p-6 text-white">
            <div className="rounded-2xl bg-white/20 p-3">
              <Bot size={30} />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold">ShopSense AI Assistant</h1>
              <p className="mt-1 text-sm text-brand-100">
                Semantic search · Recommendations · Comparisons · Review sentiment
              </p>
            </div>
          </div>

          <ChatPanel heightClass="h-[min(520px,60vh)]" />
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="rounded-2xl border border-brand-100 bg-white p-5">
              <Icon className="mb-3 text-brand-600" />
              <h3 className="font-bold text-gray-800">{title}</h3>
              <p className="mt-1 text-sm text-gray-500">{text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Chatbot;
