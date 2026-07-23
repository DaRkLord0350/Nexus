import { apiFetch } from '@/lib/api-client';
import type {
  InvoiceRead,
  OrderDetail,
  OrderListResponse,
  OrderNoteRead,
  OrderPriority,
  OrderRead,
  OrderStatusHistoryRead,
  PaymentAttemptRead,
} from '@/lib/types';

export interface OrderFilters {
  customerId?: string;
  status?: string;
  priority?: string;
  requiresManualReview?: boolean;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface OrderAddressInput {
  first_name: string;
  last_name: string;
  company?: string;
  phone?: string;
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postal_code?: string;
  country: string;
}

export interface OrderLineItemInput {
  product_id: string;
  variant_id?: string;
  warehouse_id?: string;
  quantity: number;
  unit_price?: number;
  discount_amount?: number;
  tax_amount?: number;
  gift_note?: string;
}

export interface OrderCreateInput {
  customer_id: string;
  cart_id?: string;
  currency?: string;
  billing_address: OrderAddressInput;
  shipping_address: OrderAddressInput;
  payment_method?: string;
  shipping_method?: string;
  shipping_amount?: number;
  customer_note?: string;
  gift_note?: string;
  priority?: OrderPriority;
  source?: string;
  tags?: string;
  coupon_code?: string;
  items: OrderLineItemInput[];
}

export interface OrderUpdateInput {
  priority?: OrderPriority;
  tags?: string;
  shipping_method?: string;
  customer_note?: string;
  gift_note?: string;
  fraud_score?: number;
  risk_score?: number;
  requires_manual_review?: boolean;
}

function buildQuery(filters: OrderFilters): string {
  const params = new URLSearchParams();
  if (filters.customerId) params.set('customer_id', filters.customerId);
  if (filters.status) params.set('status', filters.status);
  if (filters.priority) params.set('priority', filters.priority);
  if (filters.requiresManualReview !== undefined) params.set('requires_manual_review', String(filters.requiresManualReview));
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'created_at');
  params.set('sort_order', filters.sortOrder ?? 'desc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchOrders(filters: OrderFilters = {}): Promise<OrderListResponse> {
  return apiFetch<OrderListResponse>(`/api/v1/orders/?${buildQuery(filters)}`);
}

export async function fetchOrder(orderId: string): Promise<OrderDetail> {
  return apiFetch<OrderDetail>(`/api/v1/orders/${orderId}`);
}

export async function createOrder(data: OrderCreateInput): Promise<OrderRead> {
  return apiFetch<OrderRead>('/api/v1/orders/', { method: 'POST', json: data });
}

export async function updateOrder(orderId: string, data: OrderUpdateInput): Promise<OrderRead> {
  return apiFetch<OrderRead>(`/api/v1/orders/${orderId}`, { method: 'PATCH', json: data });
}

export async function fetchOrderHistory(orderId: string): Promise<OrderStatusHistoryRead[]> {
  return apiFetch<OrderStatusHistoryRead[]>(`/api/v1/orders/${orderId}/history`);
}

export async function fetchOrderNotes(orderId: string): Promise<OrderNoteRead[]> {
  return apiFetch<OrderNoteRead[]>(`/api/v1/orders/${orderId}/notes`);
}

export async function addOrderNote(orderId: string, note: string, isCustomerVisible = false): Promise<OrderNoteRead> {
  return apiFetch<OrderNoteRead>(`/api/v1/orders/${orderId}/notes`, { method: 'POST', json: { note, is_customer_visible: isCustomerVisible } });
}

const WORKFLOW_ACTIONS = [
  'place', 'confirm', 'process', 'pack', 'ready-to-ship', 'ship', 'out-for-delivery', 'deliver', 'partially-fulfill', 'backorder', 'resume',
] as const;

export type OrderWorkflowAction = (typeof WORKFLOW_ACTIONS)[number];

export async function applyOrderTransition(orderId: string, action: OrderWorkflowAction): Promise<OrderRead> {
  return apiFetch<OrderRead>(`/api/v1/orders/${orderId}/${action}`, { method: 'POST' });
}

export async function cancelOrder(orderId: string, reason?: string): Promise<OrderRead> {
  return apiFetch<OrderRead>(`/api/v1/orders/${orderId}/cancel`, { method: 'POST', json: { reason } });
}

export async function holdOrder(orderId: string, reason?: string): Promise<OrderRead> {
  return apiFetch<OrderRead>(`/api/v1/orders/${orderId}/hold`, { method: 'POST', json: { reason } });
}

export async function failOrder(orderId: string, reason?: string): Promise<OrderRead> {
  return apiFetch<OrderRead>(`/api/v1/orders/${orderId}/fail`, { method: 'POST', json: { reason } });
}

export async function fetchOrderPayments(orderId: string): Promise<PaymentAttemptRead[]> {
  return apiFetch<PaymentAttemptRead[]>(`/api/v1/orders/${orderId}/payments`);
}

export async function createOrderPayment(orderId: string, method: string, amount: number, gateway?: string): Promise<PaymentAttemptRead> {
  return apiFetch<PaymentAttemptRead>(`/api/v1/orders/${orderId}/payments`, { method: 'POST', json: { method, amount, gateway } });
}

export async function refundOrderPayment(orderId: string, amount: number, reason?: string): Promise<PaymentAttemptRead> {
  return apiFetch<PaymentAttemptRead>(`/api/v1/orders/${orderId}/refund-payment`, { method: 'POST', json: { amount, reason } });
}

export async function fetchOrderInvoice(orderId: string): Promise<InvoiceRead | null> {
  try {
    return await apiFetch<InvoiceRead>(`/api/v1/orders/${orderId}/invoice`);
  } catch {
    return null;
  }
}

export async function generateOrderInvoice(orderId: string): Promise<InvoiceRead> {
  return apiFetch<InvoiceRead>(`/api/v1/orders/${orderId}/invoice`, { method: 'POST' });
}

export async function fetchInvoiceHtml(invoiceId: string): Promise<string> {
  return apiFetch<string>(`/api/v1/invoices/${invoiceId}/html`);
}

export async function bulkUpdateOrderPriority(ids: string[], priority: OrderPriority): Promise<void> {
  await apiFetch(`/api/v1/orders/bulk-priority`, { method: 'POST', json: { ids, priority } });
}

export async function bulkUpdateOrderTags(ids: string[], tags: string): Promise<void> {
  await apiFetch(`/api/v1/orders/bulk-tags`, { method: 'POST', json: { ids, tags } });
}
