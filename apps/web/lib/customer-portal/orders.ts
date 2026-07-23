import { portalApiFetch, withOrg } from '@/lib/customer-portal/api-client';
import type { CustomerShipmentTrackingRead, InvoiceRead, OrderDetail, OrderListResponse } from '@/lib/types';

export async function fetchMyOrders(status?: string, limit = 20, offset = 0): Promise<OrderListResponse> {
  return portalApiFetch<OrderListResponse>(withOrg('/api/v1/customers/me/orders', { status, limit: String(limit), offset: String(offset) }));
}

export async function fetchMyOrder(orderId: string): Promise<OrderDetail> {
  return portalApiFetch<OrderDetail>(withOrg(`/api/v1/customers/me/orders/${orderId}`));
}

export async function fetchMyOrderInvoice(orderId: string): Promise<InvoiceRead | null> {
  try {
    return await portalApiFetch<InvoiceRead>(withOrg(`/api/v1/customers/me/orders/${orderId}/invoice`));
  } catch {
    return null;
  }
}

export async function fetchMyOrderInvoiceHtml(orderId: string): Promise<string> {
  return portalApiFetch<string>(withOrg(`/api/v1/customers/me/orders/${orderId}/invoice/html`));
}

export async function fetchMyOrderTracking(orderId: string): Promise<CustomerShipmentTrackingRead[]> {
  return portalApiFetch<CustomerShipmentTrackingRead[]>(withOrg(`/api/v1/customers/me/orders/${orderId}/tracking`));
}
