import { Link } from "react-router-dom";
import { Bot, Package, User } from "lucide-react";

import SentimentSummary from "../SentimentSummary";
import { formatPrice } from "../../config";
import ProductImage from "../ProductImage";

function ProductCards({ products, onNavigate }) {
  if (!products?.length) return null;
  return (
    <div className="mt-3 flex gap-3 overflow-x-auto pb-2">
      {products.map((product) => (
        <Link
          key={product.id}
          to={`/product/${product.id}`}
          onClick={onNavigate}
          className="w-40 shrink-0 overflow-hidden rounded-xl border border-brand-100 bg-white transition hover:shadow-md"
        >
          <div className="flex h-24 items-center justify-center bg-gray-50 p-2">
            {product.image_url ? (
              <ProductImage src={product.image_url} alt={product.name} className="h-full w-full object-contain" />
            ) : (
              <Package className="text-brand-300" size={32} />
            )}
          </div>
          <div className="p-2.5">
            <p className="line-clamp-2 text-xs font-semibold text-gray-800">{product.name}</p>
            <p className="mt-1 text-sm font-bold text-brand-700">{formatPrice(product.price)}</p>
            {product.positive_percentage != null && (
              <p className="mt-0.5 text-[11px] text-green-700">
                👍 {product.positive_percentage}% positive
              </p>
            )}
            {product.reason && (
              <p className="mt-0.5 line-clamp-2 text-[11px] text-gray-500">{product.reason}</p>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}

function ComparisonTable({ comparison, onNavigate }) {
  const { products, rows, verdict } = comparison;
  return (
    <div className="mt-3">
      <div className="overflow-x-auto rounded-xl border border-brand-100">
        <table className="w-full min-w-[420px] text-left text-xs">
          <thead className="bg-brand-50">
            <tr>
              <th className="p-2.5 font-semibold text-gray-500" />
              {products.map((p) => (
                <th key={p.id} className="p-2.5 font-semibold text-brand-800">
                  <Link to={`/product/${p.id}`} onClick={onNavigate} className="hover:underline">
                    {p.name}
                  </Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-50 bg-white">
            {rows.map((row) => (
              <tr key={row.label}>
                <td className="whitespace-nowrap p-2.5 font-medium text-gray-500">{row.label}</td>
                {row.values.map((value, i) => (
                  <td key={i} className="p-2.5 text-gray-700">
                    {value}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {verdict && <p className="mt-2 text-xs font-medium text-brand-800">💡 {verdict}</p>}
    </div>
  );
}

function ChatMessage({ message, onNavigate }) {
  if (message.sender === "user") {
    return (
      <div className="flex justify-end gap-2">
        <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-brand-700 px-4 py-2.5 text-sm text-white shadow-sm">
          {message.text}
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-200 text-brand-800">
          <User size={16} />
        </div>
      </div>
    );
  }

  const data = message.data || {};
  return (
    <div className="flex gap-2">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
        <Bot size={17} />
      </div>
      <div className="min-w-0 max-w-[88%] rounded-2xl rounded-bl-sm border border-brand-100 bg-white px-4 py-3 text-sm text-gray-700 shadow-sm">
        <p className="whitespace-pre-line leading-6">{data.text}</p>

        {data.details?.length > 0 && (
          <ul className="mt-2 space-y-1 text-xs text-gray-600">
            {data.details.map((line) => (
              <li key={line}>• {line}</li>
            ))}
          </ul>
        )}

        {data.type === "review_summary" && data.summary && (
          <div className="mt-3 rounded-xl bg-gray-50 p-3">
            <SentimentSummary summary={data.summary} compact />
          </div>
        )}

        {data.comparison && (
          <ComparisonTable comparison={data.comparison} onNavigate={onNavigate} />
        )}

        {!data.comparison && <ProductCards products={data.products} onNavigate={onNavigate} />}

        {data.intent && (
          <p className="mt-2 text-[10px] uppercase tracking-wide text-gray-300">
            intent: {data.intent.replace(/_/g, " ")}
          </p>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
