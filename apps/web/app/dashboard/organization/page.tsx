'use client';

import { Building2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useAuth } from '@/components/auth-provider';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormButton, FormError, FormField, FormInput, FormSuccess } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { getMyOrganization, inviteMember, listMembers, updateOrganization } from '@/lib/organizations';
import type { Organization, User } from '@/lib/types';

export default function OrganizationPage() {
  const { user } = useAuth();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [members, setMembers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('');
  const [country, setCountry] = useState('');
  const [savingOrg, setSavingOrg] = useState(false);
  const [orgSuccess, setOrgSuccess] = useState<string | null>(null);

  const [inviteEmail, setInviteEmail] = useState('');
  const [invitingMember, setInvitingMember] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const org = await getMyOrganization();
      setOrganization(org);
      setName(org.name);
      setIndustry(org.industry ?? '');
      setCountry(org.country ?? '');
      if (user) {
        try {
          setMembers(await listMembers(org.id));
        } catch {
          // Members listing requires the "users" permission; ignore if unavailable.
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load organization.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  const handleSaveOrg = async () => {
    if (!organization) return;
    setSavingOrg(true);
    setOrgSuccess(null);
    setError(null);
    try {
      const updated = await updateOrganization(organization.id, { name, industry, country });
      setOrganization(updated);
      setOrgSuccess('Organization updated.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update organization.');
    } finally {
      setSavingOrg(false);
    }
  };

  const handleInvite = async () => {
    if (!organization || !inviteEmail.trim()) return;
    setInvitingMember(true);
    setInviteSuccess(null);
    setError(null);
    try {
      await inviteMember(organization.id, inviteEmail.trim());
      setInviteSuccess(`Invitation sent to ${inviteEmail.trim()}.`);
      setInviteEmail('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to send invitation.');
    } finally {
      setInvitingMember(false);
    }
  };

  if (loading) return <SkeletonRows count={5} />;
  if (!organization) return <EmptyState icon={Building2} title="Organization not found" description={error ?? undefined} />;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Organization</h2>
      <FormError message={error} />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
          <h3 className="font-semibold text-slate-900 dark:text-white">Details</h3>
          <FormSuccess message={orgSuccess} />

          <div>
            <FormField label="Name" htmlFor="org-name" />
            <FormInput id="org-name" value={name} onChange={(e) => setName(e.target.value)} disabled={!organization} />
          </div>
          <div>
            <FormField label="Industry" htmlFor="org-industry" />
            <FormInput id="org-industry" value={industry} onChange={(e) => setIndustry(e.target.value)} />
          </div>
          <div>
            <FormField label="Country" htmlFor="org-country" />
            <FormInput id="org-country" value={country} onChange={(e) => setCountry(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm text-slate-500 dark:text-slate-400">
            <p>Slug: <span className="text-slate-900 dark:text-white">{organization.slug}</span></p>
            <p>Status: <span className="text-slate-900 dark:text-white">{organization.status}</span></p>
          </div>

          <PermissionGuard permission="settings">
            <FormButton type="button" onClick={handleSaveOrg} loading={savingOrg}>
              Save changes
            </FormButton>
          </PermissionGuard>
        </div>

        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
          <h3 className="font-semibold text-slate-900 dark:text-white">Members</h3>
          <div className="space-y-2">
            {members.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">No member list available.</p>
            ) : (
              members.map((member) => (
                <div key={member.id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950/60">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">{member.first_name} {member.last_name}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{member.email}</p>
                  </div>
                  {member.is_verified ? (
                    <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-600 dark:text-emerald-300">Verified</span>
                  ) : (
                    <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-xs text-amber-600 dark:text-amber-300">Pending</span>
                  )}
                </div>
              ))
            )}
          </div>

          <PermissionGuard permission="users">
            <div className="border-t border-slate-100 pt-4 dark:border-slate-800">
              <FormSuccess message={inviteSuccess} />
              <FormField label="Invite a teammate" htmlFor="invite-email" />
              <div className="flex gap-2">
                <FormInput
                  id="invite-email"
                  type="email"
                  placeholder="teammate@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                />
                <FormButton type="button" onClick={handleInvite} loading={invitingMember} className="w-auto shrink-0 px-4">
                  Invite
                </FormButton>
              </div>
            </div>
          </PermissionGuard>
        </div>
      </div>
    </div>
  );
}
