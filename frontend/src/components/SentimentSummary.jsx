import { ThumbsDown, ThumbsUp } from "lucide-react";

const OVERALL_STYLES = {
  positive: "bg-green-100 text-green-800",
  negative: "bg-red-100 text-red-700",
  mixed: "bg-yellow-100 text-yellow-800",
  no_reviews: "bg-gray-100 text-gray-600",
};

/** Sentiment bar + counts + theme chips. `compact` is used inside the chat. */
function SentimentSummary({ summary, compact = false }) {
  if (!summary) return null;

  const {
    total_reviews: total,
    positive_percentage: pos,
    negative_percentage: neg,
    neutral_percentage: neu,
    positive_count,
    negative_count,
    neutral_count,
    average_rating,
    overall_sentiment,
    top_positive_themes = [],
    top_negative_themes = [],
  } = summary;

  if (!total) {
    return <p className="text-sm text-gray-500">No reviews yet.</p>;
  }

  return (
    <div className={compact ? "space-y-3" : "space-y-5"}>
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${
            OVERALL_STYLES[overall_sentiment] || OVERALL_STYLES.mixed
          }`}
        >
          {overall_sentiment.replace("_", " ")}
        </span>
        <span className="text-sm text-gray-600">
          {total} reviews
          {average_rating ? ` · ${average_rating} ★ average` : ""}
        </span>
      </div>

      <div>
        <div className="flex h-3 overflow-hidden rounded-full bg-gray-100">
          <div className="bg-green-500" style={{ width: `${pos}%` }} title={`Positive ${pos}%`} />
          <div className="bg-yellow-400" style={{ width: `${neu}%` }} title={`Neutral ${neu}%`} />
          <div className="bg-red-400" style={{ width: `${neg}%` }} title={`Negative ${neg}%`} />
        </div>
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
            Positive {positive_count} ({pos}%)
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
            Neutral {neutral_count}
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
            Negative {negative_count} ({neg}%)
          </span>
        </div>
      </div>

      <div className={compact ? "space-y-2" : "grid gap-4 md:grid-cols-2"}>
        <ThemeList
          icon={<ThumbsUp size={compact ? 14 : 17} />}
          title="What customers like"
          themes={top_positive_themes}
          chipClass="bg-green-50 text-green-800 border-green-200"
          titleClass="text-green-700"
          compact={compact}
        />
        <ThemeList
          icon={<ThumbsDown size={compact ? 14 : 17} />}
          title="Common complaints"
          themes={top_negative_themes}
          chipClass="bg-red-50 text-red-700 border-red-200"
          titleClass="text-red-700"
          compact={compact}
        />
      </div>
    </div>
  );
}

function ThemeList({ icon, title, themes, chipClass, titleClass, compact }) {
  return (
    <div className={compact ? "" : "rounded-2xl border border-gray-100 p-4"}>
      <p className={`flex items-center gap-2 font-semibold ${titleClass} ${compact ? "text-xs" : "text-sm"}`}>
        {icon}
        {title}
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {themes.length ? (
          themes.map((theme) => (
            <span
              key={theme}
              className={`rounded-full border px-3 py-1 text-xs font-medium capitalize ${chipClass}`}
            >
              {theme}
            </span>
          ))
        ) : (
          <span className="text-xs text-gray-400">None mentioned</span>
        )}
      </div>
    </div>
  );
}

export default SentimentSummary;
