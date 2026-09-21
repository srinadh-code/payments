import axios from "axios";
import type {
  CreateOrderRequest,
  CreateOrderResponse,
  Product,
  VerifyPaymentRequest,
  VerifyPaymentResponse,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

export const getProduct = async (productId: number): Promise<Product> => {
  const response = await api.get<Product>(`/products/${productId}/`);
  return response.data;
};

export const createOrder = async (
  payload: CreateOrderRequest
): Promise<CreateOrderResponse> => {
  const response = await api.post<CreateOrderResponse>(
    "/create-order/",
    payload
  );
  return response.data;
};

export const verifyPayment = async (
  payload: VerifyPaymentRequest
): Promise<VerifyPaymentResponse> => {
  const response = await api.post<VerifyPaymentResponse>(
    "/verify-payment/",
    payload
  );
  return response.data;
};
