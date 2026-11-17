import { useState } from "react";
import { Package } from "lucide-react";

/**
 * Product photo with a clean placeholder when the image is missing or blocked
 * (some retailer CDNs refuse to serve their images to other sites).
 */
function ProductImage({ src, alt, className = "", iconSize = 40 }) {
  const [failedSrc, setFailedSrc] = useState(null);

  if (!src || failedSrc === src) {
    return (
      <div
        role="img"
        aria-label={alt}
        className={`${className} flex items-center justify-center bg-brand-50 text-brand-300`}
      >
        <Package size={iconSize} strokeWidth={1.4} />
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setFailedSrc(src)}
      className={className}
    />
  );
}

export default ProductImage;
