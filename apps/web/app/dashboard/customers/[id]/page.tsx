'use client';

import { ArrowLeft, MapPin, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { addCustomerAddress, deleteCustomerAddress, fetchCustomer, fetchCustomerAddresses, updateCustomer } from '@/lib/customers/customers';
import { fetchOrders } from '@/lib/orders/orders';
import type { AddressItem, CustomerItem, OrderRead } from '@/lib/types';

export default function CustomerDetailPage() {
  const params = useParams<{ id: string }>();
  const customerId = params.id;

  const [customer, setCustomer] = useState<CustomerItem | null>(null);
  const [addresses, setAddresses] = useState<AddressItem[]>([]);
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [addrFirstName, setAddrFirstName] = useState('');
  const [addrLastName, setAddrLastName] = useState('');
  const [addrLine1, setAddrLine1] = useState('');
  const [addrCity, setAddrCity] = useState('');
  const [addrCountry, setAddrCountry] = useState('US');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [customerData, addressData, ordersData] = await Promise.all([
        fetchCustomer(customerId),
        fetchCustomerAddresses(customerId),
        fetchOrders({ customerId, limit: 10 }),
      ]);
      setCustomer(customerData);
      setAddresses(addressData.items);
      setOrders(ordersData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load customer.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (customerId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId]);

  const handleToggleActive = async () => {
    if (!customer) return;
    try {
      await updateCustomer(customerId, { is_active: !customer.is_active });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update customer.');
    }
  };

  const handleAddAddress = async () => {
    if (!addrFirstName.trim() || !addrLastName.trim() || !addrLine1.trim() || !addrCity.trim()) return;
    try {
      await addCustomerAddress(customerId, { first_name: addrFirstName, last_name: addrLastName, line1: addrLine1, city: addrCity, country: addrCountry });
      setAddrFirstName('');
      setAddrLastName('');
      setAddrLine1('');
      setAddrCity('');
      setShowAddressForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to add address.');
    }
  };

  const handleDeleteAddress = async (addressId: string) => {
    if (!confirm('Delete this address?')) return;
    try {
      await deleteCustomerAddress(customerId, addressId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete address.');
    }
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/customers" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to customers
      </Link>

      <FormError message={error} />

      {!customer ? (
        <EmptyState title="Customer not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{customer.first_name} {customer.last_name}</h2>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{customer.email} · {customer.phone ?? 'No phone'}</p>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{customer.is_guest ? 'Guest account' : 'Registered account'}</p>
              </div>
              <PermissionGuard permission="customers.manage">
                <button
                  type="button"
                  onClick={handleToggleActive}
                  className={`rounded-xl px-3.5 py-2 text-sm font-semibold ${
                    customer.is_active
                      ? 'border border-red-300 text-red-600 hover:bg-red-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10'
                      : 'bg-cyan-500 text-slate-950 hover:bg-cyan-400'
                  }`}
                >
                  {customer.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </PermissionGuard>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Addresses</h3>
            <PermissionGuard permission="customers.manage">
              <button type="button" onClick={() => setShowAddressForm((v) => !v)} className="text-sm font-semibold text-cyan-600 hover:text-cyan-500 dark:text-cyan-400">
                {showAddressForm ? 'Cancel' : 'Add address'}
              </button>
            </PermissionGuard>
          </div>

          {showAddressForm ? (
            <div className="grid grid-cols-2 gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-5">
              <FormInput placeholder="First name" value={addrFirstName} onChange={(e) => setAddrFirstName(e.target.value)} />
              <FormInput placeholder="Last name" value={addrLastName} onChange={(e) => setAddrLastName(e.target.value)} />
              <FormInput placeholder="Address line 1" value={addrLine1} onChange={(e) => setAddrLine1(e.target.value)} />
              <FormInput placeholder="City" value={addrCity} onChange={(e) => setAddrCity(e.target.value)} />
              <div className="flex gap-2">
                <FormInput placeholder="US" maxLength={2} value={addrCountry} onChange={(e) => setAddrCountry(e.target.value.toUpperCase())} />
                <button type="button" onClick={handleAddAddress} className="rounded-xl bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400">Save</button>
              </div>
            </div>
          ) : null}

          {addresses.length === 0 ? (
            <EmptyState icon={MapPin} title="No addresses on file" />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {addresses.map((address) => (
                <div key={address.id} className="flex items-start justify-between rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900/60">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {address.first_name} {address.last_name} {address.is_default ? <span className="ml-1 text-xs text-cyan-600 dark:text-cyan-400">(default)</span> : null}
                    </p>
                    <p className="text-slate-500 dark:text-slate-400">{address.line1}, {address.city}, {address.country}</p>
                    <p className="text-xs uppercase text-slate-400">{address.address_type}</p>
                  </div>
                  <PermissionGuard permission="customers.manage">
                    <button type="button" onClick={() => handleDeleteAddress(address.id)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                      <Trash2 size={16} />
                    </button>
                  </PermissionGuard>
                </div>
              ))}
            </div>
          )}

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Recent orders</h3>
          {orders.length === 0 ? (
            <EmptyState title="No orders yet" />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Order #</th>
                    <th className="px-4 py-3">Total</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {orders.map((order) => (
                    <tr key={order.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                        <Link href={`/dashboard/orders/${order.id}`} className="hover:text-cyan-600 dark:hover:text-cyan-300">{order.order_number}</Link>
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{order.currency} {order.total.toFixed(2)}</td>
                      <td className="px-4 py-3 capitalize text-slate-500 dark:text-slate-400">{order.status.replace(/_/g, ' ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
