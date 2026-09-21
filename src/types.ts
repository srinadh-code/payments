export interface Product {
  id: number;
  name: string;
  price: string; // DRF DecimalField serializes as a string
  stock: number;
  image: string | null;
  created_at: string;
}

export interface CreateOrderRequest {
  product_id: number;
  customer_name: string;
  email: string;
}

export interface CreateOrderResponse {
  success: boolean;
  payment_id: number;
  order_id: string;
  amount: number; // paise
  currency: string;
  product_name: string;
  customer_name: string;
  email: string;
}

export interface VerifyPaymentRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface VerifyPaymentResponse {
  success: boolean;
  message: string;
}

export interface RazorpayCheckoutResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description?: string;
  order_id: string;
  handler: (response: RazorpayCheckoutResponse) => void;
  prefill?: {
    name?: string;
    email?: string;
    contact?: string;
  };
  theme?: {
    color?: string;
  };
  modal?: {
    ondismiss?: () => void;
  };
}

export interface RazorpayInstance {
  open: () => void;
  on: (event: string, handler: (response: unknown) => void) => void;
}

export type PaymentStatus = "idle" | "processing" | "success" | "failed";
