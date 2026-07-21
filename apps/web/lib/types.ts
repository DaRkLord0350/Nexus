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
