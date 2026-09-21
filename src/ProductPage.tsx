import { useCallback, useEffect, useState } from "react";
import { createOrder, getProduct, verifyPayment } from "./services/payment";
import type {
  PaymentStatus,
  Product,
  RazorpayCheckoutResponse,
  RazorpayOptions,
} from "./types";
import shirtPlaceholder from "./assets/shirt-placeholder.svg";
import "./ProductPage.css";

const PRODUCT_ID = 1;
const CUSTOMER_NAME = "Guest Customer";
const CUSTOMER_EMAIL = "guest@example.com";

function ProductPage() {
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [status, setStatus] = useState<PaymentStatus>("idle");

  const loadProduct = useCallback(async () => {
    try {
      const data = await getProduct(PRODUCT_ID);
      setProduct(data);
      setLoadError(null);
    } catch {
      setLoadError("Could not load product. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProduct();
  }, [loadProduct]);

  const handleBuyNow = async () => {
    if (!product || product.stock <= 0) return;

    setStatus("processing");

    try {
      const order = await createOrder({
        product_id: product.id,
        customer_name: CUSTOMER_NAME,
        email: CUSTOMER_EMAIL,
      });

      const options: RazorpayOptions = {
        key: import.meta.env.VITE_RAZORPAY_KEY_ID,
        amount: order.amount,
        currency: order.currency,
        name: "Your Store",
        description: order.product_name,
        order_id: order.order_id,
        prefill: {
          name: order.customer_name,
          email: order.email,
        },
        theme: {
          color: "#3399cc",
        },
        modal: {
          ondismiss: () => setStatus("idle"),
        },
        handler: async (response: RazorpayCheckoutResponse) => {
          try {
            const result = await verifyPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });

            setStatus(result.success ? "success" : "failed");
          } catch {
            setStatus("failed");
          } finally {
            loadProduct();
          }
        },
      };

      const razorpay = new window.Razorpay(options);
      razorpay.on("payment.failed", () => {
        setStatus("failed");
        loadProduct();
      });
      razorpay.open();
    } catch {
      setStatus("failed");
    }
  };

  if (loading) {
    return <div className="page-center">Loading…</div>;
  }

  if (loadError || !product) {
    return <div className="page-center error-text">{loadError}</div>;
  }

  const outOfStock = product.stock <= 0;

  return (
    <div className="page-center">
      <div className="product-card">
        <img
          className="product-image"
          src={product.image ?? shirtPlaceholder}
          alt={product.name}
        />

        <h1 className="product-name">{product.name}</h1>
        <p className="product-price">₹{product.price}</p>
        <p className={`product-stock ${outOfStock ? "out" : ""}`}>
          {outOfStock ? "Out of stock" : `Stock: ${product.stock}`}
        </p>

        <button
          className="buy-button"
          onClick={handleBuyNow}
          disabled={outOfStock || status === "processing"}
        >
          {status === "processing" ? "Processing…" : "Buy Now"}
        </button>

        {status === "success" && (
          <p className="status-text success">Payment Successful</p>
        )}
        {status === "failed" && (
          <p className="status-text failed">Payment Failed</p>
        )}
      </div>
    </div>
  );
}

export default ProductPage;
