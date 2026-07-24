import { apiFetch } from '@/lib/api-client';
import type { MarketplaceAnalyticsResponse } from '@/lib/types';

export async function fetchMarketplaceAnalytics(): Promise<MarketplaceAnalyticsResponse> {
  return apiFetch<MarketplaceAnalyticsResponse>('/api/v1/marketplace/analytics/dashboard');
}
