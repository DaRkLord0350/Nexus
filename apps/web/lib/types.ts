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

export type WarehouseType = 'main' | 'retail' | 'returns' | 'third_party';

export interface WarehouseItem {
  id: string;
  name: string;
  code: string;
  warehouse_type: WarehouseType;
  email?: string | null;
  phone?: string | null;
  country?: string | null;
  state?: string | null;
  city?: string | null;
  zipcode?: string | null;
  address?: string | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WarehouseListResponse {
  items: WarehouseItem[];
  total: number;
  limit: number;
  offset: number;
}

export type WarehouseZoneType = 'receiving' | 'storage' | 'picking' | 'packing' | 'returns' | 'damaged';

export interface WarehouseZoneItem {
  id: string;
  warehouse_id: string;
  name: string;
  code: string;
  zone_type: WarehouseZoneType;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WarehouseZoneListResponse {
  items: WarehouseZoneItem[];
  total: number;
  limit: number;
  offset: number;
}

export type WarehouseBinStatus = 'active' | 'full' | 'blocked' | 'inactive';

export interface WarehouseBinItem {
  id: string;
  warehouse_id: string;
  zone_id?: string | null;
  code: string;
  aisle?: string | null;
  rack?: string | null;
  shelf?: string | null;
  bin_number?: string | null;
  capacity?: number | null;
  status: WarehouseBinStatus;
  created_at: string;
  updated_at: string;
}

export interface WarehouseBinListResponse {
  items: WarehouseBinItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface InventoryItem {
  id: string;
  product_id: string;
  variant_id?: string | null;
  warehouse_id: string;
  bin_id?: string | null;
  quantity_available: number;
  quantity_reserved: number;
  quantity_incoming: number;
  quantity_damaged: number;
  quantity_returned: number;
  minimum_stock?: number | null;
  maximum_stock?: number | null;
  reorder_point?: number | null;
  average_cost?: number | null;
  last_counted_at?: string | null;
  low_stock_notified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InventoryListResponse {
  items: InventoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export type InventoryTransactionType =
  | 'receive'
  | 'sale'
  | 'return'
  | 'transfer'
  | 'adjustment'
  | 'damage'
  | 'cycle_count'
  | 'manufacturing'
  | 'purchase';

export interface InventoryTransactionItem {
  id: string;
  inventory_id: string;
  product_id: string;
  variant_id?: string | null;
  warehouse_id: string;
  type: InventoryTransactionType;
  quantity: number;
  quantity_before?: number | null;
  quantity_after?: number | null;
  reference_type?: string | null;
  reference_id?: string | null;
  user_id?: string | null;
  notes?: string | null;
  occurred_at: string;
  created_at: string;
}

export interface InventoryTransactionListResponse {
  items: InventoryTransactionItem[];
  total: number;
  limit: number;
  offset: number;
}

export type BarcodeFormat = 'ean13' | 'upc' | 'code128' | 'qr';

export interface BarcodeItem {
  id: string;
  product_id?: string | null;
  variant_id?: string | null;
  value: string;
  format: BarcodeFormat;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

export interface BarcodeListResponse {
  items: BarcodeItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface QRCodeItem {
  id: string;
  entity_type: string;
  entity_id: string;
  value: string;
  image_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface QRCodeListResponse {
  items: QRCodeItem[];
  total: number;
  limit: number;
  offset: number;
}

export type BatchStatus = 'active' | 'depleted' | 'expired' | 'quarantined' | 'recalled';

export interface BatchItem {
  id: string;
  inventory_id: string;
  product_id: string;
  variant_id?: string | null;
  warehouse_id: string;
  batch_number: string;
  manufactured_date?: string | null;
  expiry_date?: string | null;
  received_quantity: number;
  remaining_quantity: number;
  status: BatchStatus;
  cost_price?: number | null;
  created_at: string;
  updated_at: string;
}

export interface BatchListResponse {
  items: BatchItem[];
  total: number;
  limit: number;
  offset: number;
}

export type SerialStatus = 'available' | 'reserved' | 'sold' | 'returned' | 'damaged';

export interface SerialNumberItem {
  id: string;
  inventory_id: string;
  product_id: string;
  variant_id?: string | null;
  warehouse_id: string;
  batch_id?: string | null;
  bin_id?: string | null;
  serial: string;
  status: SerialStatus;
  sold_at?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SerialNumberListResponse {
  items: SerialNumberItem[];
  total: number;
  limit: number;
  offset: number;
}

export type PurchaseOrderStatus = 'draft' | 'sent' | 'partially_received' | 'received' | 'cancelled';

export interface PurchaseOrderItem {
  id: string;
  po_number: string;
  supplier_name: string;
  supplier_email?: string | null;
  supplier_phone?: string | null;
  warehouse_id: string;
  status: PurchaseOrderStatus;
  currency: string;
  subtotal: number;
  tax_amount: number;
  shipping_amount: number;
  total: number;
  expected_date?: string | null;
  sent_at?: string | null;
  received_at?: string | null;
  cancelled_at?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PurchaseOrderListResponse {
  items: PurchaseOrderItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface PurchaseOrderLineItem {
  id: string;
  purchase_order_id: string;
  product_id: string;
  variant_id?: string | null;
  quantity_ordered: number;
  quantity_received: number;
  unit_cost: number;
  tax_rate?: number | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PurchaseOrderDetail extends PurchaseOrderItem {
  items: PurchaseOrderLineItem[];
}

export type GoodsReceiptStatus = 'draft' | 'completed' | 'cancelled';

export interface GoodsReceiptItem {
  id: string;
  receipt_number: string;
  purchase_order_id?: string | null;
  warehouse_id: string;
  receiver_id?: string | null;
  received_date: string;
  status: GoodsReceiptStatus;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface GoodsReceiptListResponse {
  items: GoodsReceiptItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface GoodsReceiptLineItem {
  id: string;
  goods_receipt_id: string;
  purchase_order_item_id?: string | null;
  product_id: string;
  variant_id?: string | null;
  quantity_received: number;
  unit_cost?: number | null;
  batch_number?: string | null;
  expiry_date?: string | null;
  manufactured_date?: string | null;
  bin_id?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface GoodsReceiptDetail extends GoodsReceiptItem {
  items: GoodsReceiptLineItem[];
}

export type StockTransferStatus = 'draft' | 'packed' | 'shipped' | 'received' | 'cancelled';

export interface StockTransferItem {
  id: string;
  transfer_number: string;
  from_warehouse_id: string;
  to_warehouse_id: string;
  status: StockTransferStatus;
  shipped_at?: string | null;
  received_at?: string | null;
  cancelled_at?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StockTransferListResponse {
  items: StockTransferItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface StockTransferLineItem {
  id: string;
  stock_transfer_id: string;
  product_id: string;
  variant_id?: string | null;
  quantity_requested: number;
  quantity_shipped: number;
  quantity_received: number;
  batch_id?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StockTransferDetail extends StockTransferItem {
  items: StockTransferLineItem[];
}

export type StockAdjustmentReason = 'damage' | 'lost' | 'found' | 'audit' | 'manual';

export interface StockAdjustmentItem {
  id: string;
  adjustment_number: string;
  inventory_id: string;
  product_id: string;
  variant_id?: string | null;
  warehouse_id: string;
  bin_id?: string | null;
  quantity_delta: number;
  reason: StockAdjustmentReason;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface StockAdjustmentListResponse {
  items: StockAdjustmentItem[];
  total: number;
  limit: number;
  offset: number;
}

export type CycleCountStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled';

export interface CycleCountItem {
  id: string;
  count_number: string;
  warehouse_id: string;
  zone_id?: string | null;
  status: CycleCountStatus;
  scheduled_date?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  assigned_to?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CycleCountListResponse {
  items: CycleCountItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface CycleCountLineItem {
  id: string;
  cycle_count_id: string;
  inventory_id: string;
  product_id: string;
  variant_id?: string | null;
  bin_id?: string | null;
  expected_quantity: number;
  actual_quantity?: number | null;
  variance?: number | null;
  counted_at?: string | null;
  counted_by?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CycleCountDetail extends CycleCountItem {
  items: CycleCountLineItem[];
}

export interface ReorderRuleItem {
  id: string;
  product_id: string;
  variant_id?: string | null;
  warehouse_id: string;
  minimum_stock: number;
  maximum_stock?: number | null;
  reorder_quantity: number;
  supplier_name?: string | null;
  lead_time_days?: number | null;
  is_active: boolean;
  last_triggered_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReorderRuleListResponse {
  items: ReorderRuleItem[];
  total: number;
  limit: number;
  offset: number;
}

// ---------------------------------------------------------------------------
// Phase 4: Customers
// ---------------------------------------------------------------------------

export interface CustomerItem {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string | null;
  is_guest: boolean;
  is_active: boolean;
  is_verified: boolean;
  accepts_marketing: boolean;
  last_login_at?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerListResponse {
  items: CustomerItem[];
  total: number;
  limit: number;
  offset: number;
}

export type AddressType = 'billing' | 'shipping' | 'both';

export interface AddressItem {
  id: string;
  customer_id: string;
  label?: string | null;
  address_type: AddressType;
  first_name: string;
  last_name: string;
  company?: string | null;
  phone?: string | null;
  line1: string;
  line2?: string | null;
  city: string;
  state?: string | null;
  postal_code?: string | null;
  country: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface AddressListResponse {
  items: AddressItem[];
  total: number;
  limit: number;
  offset: number;
}

// ---------------------------------------------------------------------------
// Phase 4: Orders
// ---------------------------------------------------------------------------

export type OrderStatus =
  | 'draft'
  | 'pending'
  | 'confirmed'
  | 'processing'
  | 'packed'
  | 'ready_to_ship'
  | 'shipped'
  | 'out_for_delivery'
  | 'delivered'
  | 'cancelled'
  | 'failed'
  | 'hold'
  | 'partially_fulfilled'
  | 'backordered';

export type OrderPriority = 'low' | 'normal' | 'high' | 'urgent';
export type PaymentStatus = 'pending' | 'authorized' | 'paid' | 'partially_paid' | 'refunded' | 'partially_refunded' | 'failed';

export interface OrderRead {
  id: string;
  order_number: string;
  customer_id: string;
  cart_id?: string | null;
  status: OrderStatus;
  previous_status?: OrderStatus | null;
  priority: OrderPriority;
  currency: string;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  shipping_amount: number;
  total: number;
  amount_paid: number;
  amount_refunded: number;
  coupon_id?: string | null;
  coupon_code?: string | null;
  payment_method?: string | null;
  payment_status: PaymentStatus;
  shipping_method?: string | null;
  billing_first_name?: string | null;
  billing_last_name?: string | null;
  billing_company?: string | null;
  billing_phone?: string | null;
  billing_line1?: string | null;
  billing_line2?: string | null;
  billing_city?: string | null;
  billing_state?: string | null;
  billing_postal_code?: string | null;
  billing_country?: string | null;
  shipping_first_name?: string | null;
  shipping_last_name?: string | null;
  shipping_company?: string | null;
  shipping_phone?: string | null;
  shipping_line1?: string | null;
  shipping_line2?: string | null;
  shipping_city?: string | null;
  shipping_state?: string | null;
  shipping_postal_code?: string | null;
  shipping_country?: string | null;
  customer_note?: string | null;
  gift_note?: string | null;
  cancelled_reason?: string | null;
  tags?: string | null;
  fraud_score?: number | null;
  risk_score?: number | null;
  requires_manual_review: boolean;
  source: string;
  placed_at?: string | null;
  confirmed_at?: string | null;
  packed_at?: string | null;
  shipped_at?: string | null;
  delivered_at?: string | null;
  cancelled_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderLineItem {
  id: string;
  order_id: string;
  product_id: string;
  variant_id?: string | null;
  warehouse_id?: string | null;
  sku: string;
  product_name: string;
  quantity: number;
  quantity_fulfilled: number;
  quantity_returned: number;
  unit_price: number;
  discount_amount: number;
  tax_amount: number;
  total: number;
  gift_note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderStatusHistoryRead {
  id: string;
  order_id: string;
  from_status?: string | null;
  to_status: string;
  notes?: string | null;
  changed_by?: string | null;
  changed_at: string;
}

export interface OrderNoteRead {
  id: string;
  order_id: string;
  note: string;
  is_customer_visible: boolean;
  created_by?: string | null;
  created_at: string;
}

export interface OrderDetail extends OrderRead {
  items: OrderLineItem[];
  status_history: OrderStatusHistoryRead[];
  notes: OrderNoteRead[];
}

export interface OrderListResponse {
  items: OrderRead[];
  total: number;
  limit: number;
  offset: number;
}

// ---------------------------------------------------------------------------
// Phase 4: Payments & Invoices
// ---------------------------------------------------------------------------

export type PaymentAttemptStatus = 'pending' | 'authorized' | 'captured' | 'failed' | 'refunded' | 'cancelled';

export interface PaymentAttemptRead {
  id: string;
  order_id: string;
  method: string;
  gateway: string;
  status: PaymentAttemptStatus;
  amount: number;
  currency: string;
  gateway_reference?: string | null;
  failure_reason?: string | null;
  idempotency_key?: string | null;
  initiated_at: string;
  completed_at?: string | null;
  created_at: string;
}

export type InvoiceStatus = 'issued' | 'paid' | 'void';

export interface InvoiceRead {
  id: string;
  order_id: string;
  invoice_number: string;
  status: InvoiceStatus;
  currency: string;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  shipping_amount: number;
  total: number;
  amount_paid: number;
  amount_due: number;
  issued_at?: string | null;
  due_at?: string | null;
  voided_at?: string | null;
  void_reason?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvoiceListResponse {
  items: InvoiceRead[];
  total: number;
  limit: number;
  offset: number;
}

// ---------------------------------------------------------------------------
// Phase 4: Returns & Refunds
// ---------------------------------------------------------------------------

export type ReturnStatus = 'requested' | 'approved' | 'rejected' | 'awaiting_pickup' | 'in_transit' | 'received' | 'inspecting' | 'completed' | 'cancelled';
export type ReturnResolution = 'refund' | 'replacement' | 'exchange' | 'repair' | 'store_credit';
export type ReturnItemCondition = 'unopened' | 'opened' | 'damaged' | 'defective';

export interface ReturnItemRead {
  id: string;
  return_request_id: string;
  order_item_id: string;
  product_id: string;
  variant_id?: string | null;
  quantity: number;
  reason_code?: string | null;
  condition?: ReturnItemCondition | null;
  image_urls?: string | null;
  restocked: boolean;
  restocked_quantity: number;
  created_at: string;
  updated_at: string;
}

export interface ReturnRequestRead {
  id: string;
  return_number: string;
  order_id: string;
  customer_id: string;
  warehouse_id?: string | null;
  status: ReturnStatus;
  resolution?: ReturnResolution | null;
  reason_code: string;
  reason_notes?: string | null;
  inspection_notes?: string | null;
  inspected_by?: string | null;
  inspected_at?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  rejected_reason?: string | null;
  requested_at: string;
  completed_at?: string | null;
  cancelled_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReturnRequestDetail extends ReturnRequestRead {
  items: ReturnItemRead[];
}

export interface ReturnRequestListResponse {
  items: ReturnRequestRead[];
  total: number;
  limit: number;
  offset: number;
}

export type RefundMethod = 'original_payment' | 'store_credit' | 'wallet' | 'bank_transfer';
export type RefundStatus = 'requested' | 'approved' | 'rejected' | 'processing' | 'completed' | 'failed';

export interface RefundItemRead {
  id: string;
  refund_id: string;
  order_item_id: string;
  quantity?: number | null;
  amount: number;
  created_at: string;
}

export interface RefundRead {
  id: string;
  refund_number: string;
  order_id: string;
  return_request_id?: string | null;
  customer_id: string;
  payment_attempt_id?: string | null;
  method: RefundMethod;
  status: RefundStatus;
  amount: number;
  currency: string;
  reason?: string | null;
  requested_by?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  rejected_reason?: string | null;
  processed_at?: string | null;
  requested_at: string;
  created_at: string;
  updated_at: string;
}

export interface RefundDetail extends RefundRead {
  items: RefundItemRead[];
}

export interface RefundListResponse {
  items: RefundRead[];
  total: number;
  limit: number;
  offset: number;
}

// ---------------------------------------------------------------------------
// Phase 5: Shipping
// ---------------------------------------------------------------------------

export interface ShippingProviderRead {
  id: string;
  name: string;
  code: string;
  provider_type: string;
  is_active: boolean;
  is_default: boolean;
  priority: number;
  supports_cod: boolean;
  supports_insurance: boolean;
  supports_reverse_pickup: boolean;
  supports_international: boolean;
  base_rate?: number | null;
  base_transit_days?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ShippingProviderListResponse {
  items: ShippingProviderRead[];
  total: number;
  limit: number;
  offset: number;
}

export type ShipmentStatus =
  | 'pending' | 'label_generated' | 'picked_up' | 'in_transit' | 'out_for_delivery'
  | 'delivered' | 'failed_delivery' | 'returned_to_origin' | 'cancelled';

export interface ShipmentItemRead {
  id: string;
  shipment_id: string;
  order_item_id: string;
  product_id: string;
  variant_id?: string | null;
  quantity: number;
  sku: string;
  product_name: string;
}

export interface ShipmentRead {
  id: string;
  shipment_number: string;
  order_id: string;
  warehouse_id: string;
  shipping_provider_id?: string | null;
  status: ShipmentStatus;
  tracking_number?: string | null;
  carrier_name?: string | null;
  service_type?: string | null;
  weight?: number | null;
  length?: number | null;
  width?: number | null;
  height?: number | null;
  shipping_cost: number;
  insurance_amount?: number | null;
  is_cod: boolean;
  cod_amount?: number | null;
  expected_delivery_date?: string | null;
  picked_up_at?: string | null;
  delivered_at?: string | null;
  cancelled_at?: string | null;
  delivery_attempts: number;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ShipmentDetail extends ShipmentRead {
  items: ShipmentItemRead[];
}

export interface ShipmentListResponse {
  items: ShipmentRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface CustomerShipmentTrackingRead extends ShipmentDetail {
  tracking_events: ShipmentTrackingEventRead[];
}

export interface ShipmentTrackingEventRead {
  id: string;
  shipment_id: string;
  status: string;
  description?: string | null;
  location?: string | null;
  occurred_at: string;
  source: string;
  created_at: string;
}

export type PickupStatus = 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'missed';

export interface PickupRead {
  id: string;
  pickup_number: string;
  warehouse_id: string;
  shipping_provider_id?: string | null;
  status: PickupStatus;
  scheduled_date: string;
  time_slot?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  notes?: string | null;
  completed_at?: string | null;
  cancelled_at?: string | null;
  cancelled_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PickupListResponse {
  items: PickupRead[];
  total: number;
  limit: number;
  offset: number;
}

export type ShippingRuleConditionType = 'weight_greater_than' | 'weight_less_than' | 'is_cod' | 'destination_state' | 'destination_country' | 'order_value_greater_than';
export type ShippingRuleActionType = 'assign_provider' | 'exclude_provider' | 'prefer_warehouse';

export interface ShippingRuleRead {
  id: string;
  name: string;
  priority: number;
  is_active: boolean;
  condition_type: ShippingRuleConditionType;
  condition_value: string;
  action_type: ShippingRuleActionType;
  action_value: string;
}

export interface ShippingRuleListResponse {
  items: ShippingRuleRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface ShippingRateRead {
  id: string;
  shipping_provider_id: string;
  name: string;
  origin_country?: string | null;
  destination_country?: string | null;
  destination_state?: string | null;
  min_weight?: number | null;
  max_weight?: number | null;
  base_price: number;
  price_per_kg?: number | null;
  cod_fee?: number | null;
  insurance_fee?: number | null;
  transit_days_min?: number | null;
  transit_days_max?: number | null;
  delivery_rating?: number | null;
  is_active: boolean;
}

export interface ShippingRateListResponse {
  items: ShippingRateRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface RateQuote {
  shipping_provider_id: string;
  provider_name: string;
  rate_id?: string | null;
  cost: number;
  transit_days_min?: number | null;
  transit_days_max?: number | null;
  supports_cod: boolean;
  supports_insurance: boolean;
  delivery_rating?: number | null;
  recommended: boolean;
  score: number;
}

export interface RateCompareResponse {
  quotes: RateQuote[];
}

export type ReturnShipmentStatus = 'pending' | 'label_generated' | 'reverse_pickup_scheduled' | 'in_transit' | 'received' | 'cancelled';

export interface ReturnShipmentRead {
  id: string;
  return_shipment_number: string;
  return_request_id: string;
  warehouse_id: string;
  shipping_provider_id?: string | null;
  status: ReturnShipmentStatus;
  tracking_number?: string | null;
  carrier_name?: string | null;
  pickup_contact_name?: string | null;
  pickup_contact_phone?: string | null;
  pickup_line1?: string | null;
  pickup_city?: string | null;
  pickup_state?: string | null;
  pickup_postal_code?: string | null;
  pickup_country?: string | null;
  reverse_pickup_scheduled_at?: string | null;
  reverse_pickup_completed_at?: string | null;
  received_at?: string | null;
  cancelled_at?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReturnShipmentListResponse {
  items: ReturnShipmentRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface CourierPerformanceStats {
  shipping_provider_id: string;
  provider_name: string;
  total_shipments: number;
  delivered_count: number;
  delivered_rate: number;
  failed_delivery_count: number;
  failed_delivery_rate: number;
  cod_count: number;
  cod_rate: number;
  avg_transit_days?: number | null;
  total_shipping_cost: number;
  avg_shipping_cost: number;
  sla_met_count: number;
  sla_met_rate?: number | null;
}

export interface CourierPerformanceSummary {
  total_shipments: number;
  delivered_count: number;
  delivered_rate: number;
  failed_delivery_count: number;
  failed_delivery_rate: number;
  cod_count: number;
  cod_rate: number;
  total_shipping_cost: number;
}

export interface CourierPerformanceResponse {
  date_from?: string | null;
  date_to?: string | null;
  summary: CourierPerformanceSummary;
  providers: CourierPerformanceStats[];
}

export type MarketplaceConnectorType = 'woocommerce' | 'amazon' | 'flipkart' | 'shopify' | 'etsy' | 'ebay' | 'other';

export interface MarketplaceConnectorRead {
  id: string;
  name: string;
  code: string;
  connector_type: string;
  is_active: boolean;
  store_url?: string | null;
  auto_sync_products: boolean;
  auto_sync_orders: boolean;
  auto_sync_inventory: boolean;
  auto_sync_prices: boolean;
  sync_interval_minutes: number;
  last_sync_at?: string | null;
  last_sync_status?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MarketplaceConnectorListResponse {
  items: MarketplaceConnectorRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface MarketplaceProductLinkRead {
  id: string;
  marketplace_connector_id: string;
  product_id: string;
  external_id?: string | null;
  external_sku?: string | null;
  external_url?: string | null;
  sync_status: string;
  last_synced_at?: string | null;
  last_error?: string | null;
  last_synced_price?: number | null;
  last_synced_quantity?: number | null;
  created_at: string;
  updated_at: string;
}

export interface MarketplaceProductLinkListResponse {
  items: MarketplaceProductLinkRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface MarketplaceOrderLinkRead {
  id: string;
  marketplace_connector_id: string;
  order_id?: string | null;
  external_order_id: string;
  external_order_number?: string | null;
  status: string;
  last_error?: string | null;
  imported_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MarketplaceOrderLinkListResponse {
  items: MarketplaceOrderLinkRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface MarketplaceSyncLogRead {
  id: string;
  marketplace_connector_id: string;
  sync_type: string;
  status: string;
  triggered_by: string;
  items_processed: number;
  items_succeeded: number;
  items_failed: number;
  started_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  created_at: string;
}

export interface MarketplaceSyncLogListResponse {
  items: MarketplaceSyncLogRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface MarketplaceWebhookEventRead {
  id: string;
  marketplace_connector_id: string;
  event_type: string;
  status: string;
  retry_count: number;
  next_retry_at?: string | null;
  last_error?: string | null;
  received_at: string;
  processed_at?: string | null;
}

export interface MarketplaceWebhookEventListResponse {
  items: MarketplaceWebhookEventRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface MarketplaceConnectorStats {
  marketplace_connector_id: string;
  connector_name: string;
  connector_type: string;
  total_syncs: number;
  successful_syncs: number;
  sync_success_rate: number;
  failed_syncs: number;
  orders_imported: number;
  orders_failed: number;
  revenue_imported: number;
  products_linked: number;
  products_failed: number;
  avg_sync_duration_seconds?: number | null;
}

export interface MarketplaceAnalyticsSummary {
  total_syncs: number;
  sync_success_rate: number;
  total_orders_imported: number;
  total_revenue_imported: number;
  pending_webhook_retries: number;
}

export interface MarketplaceAnalyticsResponse {
  date_from?: string | null;
  date_to?: string | null;
  summary: MarketplaceAnalyticsSummary;
  connectors: MarketplaceConnectorStats[];
}
