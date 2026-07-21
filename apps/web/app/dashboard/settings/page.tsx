'use client';

import { Settings as SettingsIcon } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '@/components/auth-provider';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormButton, FormError, FormField, FormInput, FormSuccess } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { getMyOrganization, listMembers } from '@/lib/organizations';
import { getNotificationPreferences, updateNotificationPreference, type NotificationChannel } from '@/lib/notifications';
import { getAccessToken } from '@/lib/api-client';
import { assignRole, createRole, listRoles, removeRole } from '@/lib/rbac';
import type { NotificationPreferenceItem, Role, User } from '@/lib/types';

const ALL_CHANNELS: NotificationChannel[] = ['in_app', 'email', 'sms', 'database'];

export default function SettingsPage() {
  const { hasPermission, isLoading: authLoading } = useAuth();
  const [roles, setRoles] = useState<Role[]>([]);
  const [members, setMembers] = useState<User[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [roleName, setRoleName] = useState('');
  const [roleDescription, setRoleDescription] = useState('');
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [creatingRole, setCreatingRole] = useState(false);
  const [roleSuccess, setRoleSuccess] = useState<string | null>(null);

  const [assignUserId, setAssignUserId] = useState('');
  const [assignRoleId, setAssignRoleId] = useState('');
  const [assignBusy, setAssignBusy] = useState(false);
  const [assignSuccess, setAssignSuccess] = useState<string | null>(null);

  const availablePermissions = useMemo(() => {
    const set = new Set<string>();
    roles.forEach((role) => role.permissions.forEach((code) => set.add(code)));
    return Array.from(set).sort();
  }, [roles]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [roleList, org] = await Promise.all([listRoles(), getMyOrganization()]);
      setRoles(roleList);
      if (hasPermission('users')) {
        try {
          setMembers(await listMembers(org.id));
        } catch {
          // ignore
        }
      }
      const token = getAccessToken();
      setPreferences(await getNotificationPreferences(token));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authLoading) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading]);

  const handleCreateRole = async () => {
    if (!roleName.trim()) return;
    setCreatingRole(true);
    setRoleSuccess(null);
    setError(null);
    try {
      await createRole(roleName.trim(), roleDescription.trim(), selectedPermissions);
      setRoleSuccess(`Role "${roleName.trim()}" created.`);
      setRoleName('');
      setRoleDescription('');
      setSelectedPermissions([]);
      setRoles(await listRoles());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create role.');
    } finally {
      setCreatingRole(false);
    }
  };

  const togglePermission = (code: string) => {
    setSelectedPermissions((current) => (current.includes(code) ? current.filter((c) => c !== code) : [...current, code]));
  };

  const handleAssign = async (action: 'assign' | 'remove') => {
    if (!assignUserId || !assignRoleId) return;
    setAssignBusy(true);
    setAssignSuccess(null);
    setError(null);
    try {
      if (action === 'assign') {
        await assignRole(assignRoleId, assignUserId);
        setAssignSuccess('Role assigned.');
      } else {
        await removeRole(assignRoleId, assignUserId);
        setAssignSuccess('Role removed.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update role assignment.');
    } finally {
      setAssignBusy(false);
    }
  };

  const handleTogglePreference = async (channel: NotificationChannel, currentlyEnabled: boolean) => {
    const token = getAccessToken();
    const updated = await updateNotificationPreference(channel, !currentlyEnabled, token);
    setPreferences((current) => {
      const withoutChannel = current.filter((p) => p.channel !== channel);
      return [...withoutChannel, updated];
    });
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Settings</h2>
      <FormError message={error} />

      <div className="rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
        <h3 className="mb-4 font-semibold text-slate-900 dark:text-white">Notification preferences</h3>
        <div className="grid gap-3 sm:grid-cols-2">
          {ALL_CHANNELS.map((channel) => {
            const pref = preferences.find((p) => p.channel === channel);
            const enabled = pref ? pref.enabled : true;
            return (
              <button
                key={channel}
                type="button"
                onClick={() => handleTogglePreference(channel, enabled)}
                className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-950/60"
              >
                <span className="capitalize text-slate-700 dark:text-slate-200">{channel.replace('_', ' ')}</span>
                <span className={`h-5 w-9 rounded-full transition ${enabled ? 'bg-cyan-500' : 'bg-slate-300 dark:bg-slate-700'}`}>
                  <span className={`block h-5 w-5 rounded-full bg-white shadow transition ${enabled ? 'translate-x-4' : 'translate-x-0'}`} />
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <PermissionGuard
        permission="settings"
        fallback={<EmptyState icon={SettingsIcon} title="Roles are managed by admins" description="You don't have permission to manage roles." />}
      >
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <h3 className="font-semibold text-slate-900 dark:text-white">Roles</h3>
            <FormSuccess message={roleSuccess} />
            <div className="space-y-2">
              {roles.map((role) => (
                <div key={role.id} className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950/60">
                  <p className="font-medium text-slate-900 dark:text-white">
                    {role.name} {role.built_in ? <span className="text-xs text-slate-400">(built-in)</span> : null}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{role.permissions.join(', ') || 'No permissions'}</p>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-100 pt-4 dark:border-slate-800">
              <p className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">Create a role</p>
              <div className="space-y-3">
                <div>
                  <FormField label="Name" htmlFor="role-name" />
                  <FormInput id="role-name" value={roleName} onChange={(e) => setRoleName(e.target.value)} />
                </div>
                <div>
                  <FormField label="Description" htmlFor="role-description" />
                  <FormInput id="role-description" value={roleDescription} onChange={(e) => setRoleDescription(e.target.value)} />
                </div>
                <div>
                  <p className="mb-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">Permissions</p>
                  <div className="flex flex-wrap gap-2">
                    {availablePermissions.map((code) => (
                      <button
                        key={code}
                        type="button"
                        onClick={() => togglePermission(code)}
                        className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                          selectedPermissions.includes(code)
                            ? 'border-cyan-500 bg-cyan-500/10 text-cyan-600 dark:text-cyan-300'
                            : 'border-slate-300 text-slate-600 dark:border-slate-700 dark:text-slate-300'
                        }`}
                      >
                        {code}
                      </button>
                    ))}
                  </div>
                </div>
                <FormButton type="button" onClick={handleCreateRole} loading={creatingRole}>
                  Create role
                </FormButton>
              </div>
            </div>
          </div>

          <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <h3 className="font-semibold text-slate-900 dark:text-white">Role assignments</h3>
            <FormSuccess message={assignSuccess} />
            <div className="space-y-3">
              <div>
                <FormField label="Member" htmlFor="assign-user" />
                <select
                  id="assign-user"
                  value={assignUserId}
                  onChange={(e) => setAssignUserId(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
                >
                  <option value="">Select a member</option>
                  {members.map((member) => (
                    <option key={member.id} value={member.id}>
                      {member.first_name} {member.last_name} ({member.email})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <FormField label="Role" htmlFor="assign-role" />
                <select
                  id="assign-role"
                  value={assignRoleId}
                  onChange={(e) => setAssignRoleId(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
                >
                  <option value="">Select a role</option>
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>{role.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2">
                <FormButton type="button" onClick={() => handleAssign('assign')} loading={assignBusy}>
                  Assign
                </FormButton>
                <FormButton
                  type="button"
                  onClick={() => handleAssign('remove')}
                  loading={assignBusy}
                  className="bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                >
                  Remove
                </FormButton>
              </div>
            </div>
          </div>
        </div>
      </PermissionGuard>
    </div>
  );
}
