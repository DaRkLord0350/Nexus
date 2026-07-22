export interface DashboardMetric {
  id: string;
  title: string;
  value: number;
  subtitle?: string;
}

export interface DashboardActivityItem {
  id: string;
  user_id: string;
  user_name: string;
  device_name?: string | null;
  ip_address?: string | null;
  last_active_at: string;
  status: string;
}

export interface DashboardSummary {
  week_start: string;
  generated_at: string;
}

export interface OrganizationBrief {
  id: string;
  name: string;
  slug: string;
  status: string;
}

export interface NotificationItem {
  id: string;
  user_id: string;
  actor_id?: string | null;
  title: string;
  message: string;
  type: string;
  channel: string;
  metadata?: Record<string, unknown> | null;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: NotificationItem[];
}

export interface NotificationPreferenceItem {
  channel: string;
  enabled: boolean;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface DashboardResponse {
  organization: OrganizationBrief | null;
  metrics: DashboardMetric[];
  recent_activity: DashboardActivityItem[];
  summary: DashboardSummary;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string | null;
  logo?: string | null;
  industry?: string | null;
  country?: string | null;
  timezone?: string | null;
  currency?: string | null;
  subscription?: string | null;
  settings?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  code: string;
  name?: string | null;
  description?: string | null;
}

export interface Role {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  built_in: boolean;
  permissions: string[];
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface FileItem {
  id: string;
  name: string;
  original_filename?: string | null;
  extension?: string | null;
  folder_id: string | null;
  object_key: string;
  storage_provider: string;
  bucket?: string | null;
  content_type: string;
  size_bytes: number;
  checksum?: string | null;
  file_metadata?: Record<string, unknown> | null;
  visibility: 'private' | 'public';
  uploaded_by: string;
  created_at: string;
  updated_at: string;
}

export interface FolderItem {
  id: string;
  name: string;
  path: string;
  parent_folder_id: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BreadcrumbItem {
  id: string;
  name: string;
}

export interface FileListResponse {
  files: FileItem[];
}

export interface SearchResponse {
  files: FileItem[];
  folders: FolderItem[];
}

export interface AuditLogItem {
  id: string;
  organization_id: string;
  user_id: string | null;
  action: string;
  module: string;
  entity: string | null;
  entity_id: string | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  request_id: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  items: AuditLogItem[];
  total: number;
  limit: number;
  offset: number;
}

export type CategoryStatus = 'draft' | 'active' | 'archived';

export interface CategoryItem {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  parent_id: string | null;
  path: string;
  image_url?: string | null;
  banner_url?: string | null;
  sort_order: number;
  is_featured: boolean;
  is_visible: boolean;
  status: CategoryStatus;
  seo_title?: string | null;
  seo_description?: string | null;
  seo_keywords?: string | null;
  og_image_url?: string | null;
  canonical_url?: string | null;
  no_index: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryTreeNode extends CategoryItem {
  children: CategoryTreeNode[];
}

export interface CategoryListResponse {
  items: CategoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface CategoryBreadcrumbItem {
  id: string;
  name: string;
  slug: string;
}

export type BrandStatus = 'draft' | 'active' | 'archived';

export interface BrandItem {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  logo_url?: string | null;
  website?: string | null;
  is_featured: boolean;
  status: BrandStatus;
  seo_title?: string | null;
  seo_description?: string | null;
  seo_keywords?: string | null;
  og_image_url?: string | null;
  canonical_url?: string | null;
  no_index: boolean;
  created_at: string;
  updated_at: string;
}

export interface BrandListResponse {
  items: BrandItem[];
  total: number;
  limit: number;
  offset: number;
}

export type AttributeInputType = 'select' | 'text' | 'number' | 'boolean';

export interface AttributeItem {
  id: string;
  name: string;
  code: string;
  input_type: AttributeInputType;
  is_variant_attribute: boolean;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AttributeListResponse {
  items: AttributeItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface AttributeValueItem {
  id: string;
  attribute_id: string;
  value: string;
  slug: string;
  color_hex?: string | null;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type ProductStatus = 'draft' | 'published' | 'archived';

export interface TagItem {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface TagListResponse {
  items: TagItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductTypeItem {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductTypeListResponse {
  items: ProductTypeItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductTypeAttributeItem {
  attribute_id: string;
  name: string;
  code: string;
  is_required: boolean;
  sort_order: number;
}

export type ChannelType = 'online_store' | 'pos' | 'mobile_app' | 'marketplace' | 'social' | 'other';

export interface ChannelItem {
  id: string;
  name: string;
  code: string;
  channel_type: ChannelType;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChannelListResponse {
  items: ChannelItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductChannelItem {
  channel_id: string;
  name: string;
  code: string;
  channel_type: ChannelType;
  is_published: boolean;
  published_at?: string | null;
}

export type CustomFieldEntityType = 'product' | 'variant' | 'category' | 'brand' | 'collection';
export type CustomFieldType = 'text' | 'number' | 'boolean' | 'date' | 'select' | 'json';

export interface CustomFieldDefinitionItem {
  id: string;
  entity_type: CustomFieldEntityType;
  name: string;
  key: string;
  field_type: CustomFieldType;
  options?: string[] | null;
  is_required: boolean;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomFieldDefinitionListResponse {
  items: CustomFieldDefinitionItem[];
  total: number;
}

export interface CustomFieldValueItem {
  definition_id: string;
  key: string;
  name: string;
  field_type: CustomFieldType;
  value: unknown;
}

export interface ProductItem {
  id: string;
  name: string;
  slug: string;
  sku: string;
  barcode?: string | null;
  brand_id?: string | null;
  category_id?: string | null;
  tax_class_id?: string | null;
  product_type_id?: string | null;
  description?: string | null;
  short_description?: string | null;
  status: ProductStatus;
  seo_title?: string | null;
  seo_description?: string | null;
  seo_keywords?: string | null;
  og_image_url?: string | null;
  canonical_url?: string | null;
  no_index: boolean;
  length?: number | null;
  width?: number | null;
  height?: number | null;
  dimension_unit?: string | null;
  weight?: number | null;
  weight_unit?: string | null;
  origin_country?: string | null;
  vendor?: string | null;
  tags: TagItem[];
  search_keywords?: string | null;
  track_inventory: boolean;
  allow_backorders: boolean;
  has_variants: boolean;
  is_featured: boolean;
  published_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  items: ProductItem[];
  total: number;
  limit: number;
  offset: number;
}

export type VariantStatus = 'active' | 'archived';

export interface VariantItem {
  id: string;
  product_id: string;
  sku: string;
  barcode?: string | null;
  weight?: number | null;
  weight_unit?: string | null;
  status: VariantStatus;
  is_default: boolean;
  sort_order: number;
  attribute_values: AttributeValueItem[];
  created_at: string;
  updated_at: string;
}

export interface VariantListResponse {
  items: VariantItem[];
  total: number;
  limit: number;
  offset: number;
}

export type MediaType = 'image' | 'video' | 'pdf' | 'model_3d';

export interface MediaItem {
  id: string;
  product_id?: string | null;
  variant_id?: string | null;
  media_type: MediaType;
  object_key: string;
  storage_provider: string;
  bucket?: string | null;
  content_type: string;
  size_bytes: number;
  checksum?: string | null;
  thumbnail_key?: string | null;
  alt_text?: string | null;
  is_primary: boolean;
  sort_order: number;
  uploaded_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MediaListResponse {
  items: MediaItem[];
}

export type CollectionType = 'manual' | 'dynamic';
export type CollectionStatus = 'draft' | 'active' | 'archived';

export interface CollectionRuleCondition {
  field: 'category_id' | 'brand_id' | 'status' | 'is_featured' | 'has_variants' | 'tag';
  operator: 'eq' | 'contains';
  value: unknown;
}

export interface CollectionItem {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  image_url?: string | null;
  collection_type: CollectionType;
  rules?: CollectionRuleCondition[] | null;
  status: CollectionStatus;
  is_featured: boolean;
  sort_order: number;
  seo_title?: string | null;
  seo_description?: string | null;
  seo_keywords?: string | null;
  og_image_url?: string | null;
  canonical_url?: string | null;
  no_index: boolean;
  created_at: string;
  updated_at: string;
}

export interface CollectionListResponse {
  items: CollectionItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductPriceItem {
  id: string;
  product_id: string;
  variant_id?: string | null;
  currency: string;
  mrp?: number | null;
  selling_price: number;
  cost_price?: number | null;
  compare_price?: number | null;
  min_price?: number | null;
  max_price?: number | null;
  customer_group?: string | null;
  region?: string | null;
  effective_from?: string | null;
  effective_to?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductPriceListResponse {
  items: ProductPriceItem[];
  total: number;
  limit: number;
  offset: number;
}

export type TaxType = 'gst' | 'vat' | 'sales_tax' | 'other';

export interface TaxClassItem {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaxClassListResponse {
  items: TaxClassItem[];
  total: number;
  limit: number;
  offset: number;
}

export type CouponDiscountType = 'percentage' | 'fixed_amount' | 'free_shipping' | 'buy_x_get_y';

export interface CouponItem {
  id: string;
  code: string;
  name?: string | null;
  description?: string | null;
  discount_type: CouponDiscountType;
  discount_value?: number | null;
  buy_quantity?: number | null;
  get_quantity?: number | null;
  get_discount_percentage?: number | null;
  min_order_amount?: number | null;
  max_discount_amount?: number | null;
  usage_limit?: number | null;
  usage_limit_per_customer?: number | null;
  used_count: number;
  starts_at?: string | null;
  expires_at?: string | null;
  is_active: boolean;
  product_ids: string[];
  category_ids: string[];
  collection_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface CouponListResponse {
  items: CouponItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface TaxRateItem {
  id: string;
  tax_class_id: string;
  country: string;
  state?: string | null;
  rate: number;
  tax_type: TaxType;
  is_inclusive: boolean;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
