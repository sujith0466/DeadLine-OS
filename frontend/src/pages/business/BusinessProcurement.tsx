import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ShoppingCart,
  Plus,
  Search,
  FileText,
  CheckCircle2,
  XCircle,
  Send,
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { OperationsSubNav } from '../../components/Business/OperationsSubNav';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { BusinessEmptyState } from '../../components/Business/BusinessEmptyState';
import { BusinessLoadingState } from '../../components/Business/BusinessLoadingState';
import { BusinessErrorState } from '../../components/Business/BusinessErrorState';

interface PurchaseRequest {
  id: string;
  request_number: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  location_id: string;
  location_name: string;
  requested_quantity: string;
  estimated_unit_price: string;
  estimated_total_price: string;
  currency: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'ORDERED' | 'CANCELLED';
  reason?: string;
  requester_name?: string;
  approver_name?: string;
  approval_notes?: string;
  approved_at?: string;
  purchase_order_id?: string;
  created_at: string;
}

interface PurchaseOrderLine {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  product_unit?: string;
  ordered_quantity: string;
  received_quantity: string;
  unit_price: string;
  total_price: string;
  status: string;
}

interface PurchaseOrder {
  id: string;
  po_number: string;
  supplier_partner_id: string;
  supplier_name: string;
  destination_location_id: string;
  destination_location_name: string;
  order_date: string;
  expected_delivery_date?: string;
  subtotal_amount: string;
  tax_amount: string;
  total_amount: string;
  currency: string;
  payment_terms: string;
  status: 'DRAFT' | 'APPROVED' | 'SENT_TO_SUPPLIER' | 'ACKNOWLEDGED' | 'PARTIALLY_RECEIVED' | 'FULLY_RECEIVED' | 'CLOSED' | 'CANCELLED';
  notes?: string;
  creator_name?: string;
  approver_name?: string;
  approved_at?: string;
  sent_at?: string;
  created_at: string;
  lines?: PurchaseOrderLine[];
}

export const BusinessProcurement: React.FC = () => {
  const { role } = useBusinessAuth();
  const [activeTab, setActiveTab] = useState<'orders' | 'requests'>('orders');

  // Data states
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [requests, setRequests] = useState<PurchaseRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Auxiliary data for dropdowns
  const [products, setProducts] = useState<any[]>([]);
  const [locations, setLocations] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);

  // Search and filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Drawers and Modals
  const [selectedOrder, setSelectedOrder] = useState<PurchaseOrder | null>(null);
  const [selectedRequest, setSelectedRequest] = useState<PurchaseRequest | null>(null);
  const [showCreatePRModal, setShowCreatePRModal] = useState(false);
  const [showCreatePOModal, setShowCreatePOModal] = useState(false);
  const [showConvertModal, setShowConvertModal] = useState(false);
  const [convertingRequest, setConvertingRequest] = useState<PurchaseRequest | null>(null);

  // Forms
  const [prForm, setPrForm] = useState({
    product_id: '',
    location_id: '',
    requested_quantity: '1',
    estimated_unit_price: '',
    priority: 'MEDIUM',
    reason: '',
  });

  const [poForm, setPoForm] = useState({
    supplier_partner_id: '',
    destination_location_id: '',
    order_date: new Date().toISOString().split('T')[0],
    expected_delivery_date: '',
    payment_terms: 'NET_30',
    notes: '',
    lines: [{ product_id: '', ordered_quantity: '1', unit_price: '0.00' }],
  });

  const [convertForm, setConvertForm] = useState({
    supplier_partner_id: '',
    expected_delivery_date: '',
    payment_terms: 'NET_30',
    unit_price: '',
  });

  const isAdminOrOwner = role === 'OWNER' || role === 'ADMIN';

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [prRes, poRes, prodRes, locRes, suppRes] = await Promise.all([
        api.listPurchaseRequests(),
        api.listPurchaseOrders(),
        api.listProducts({ status: 'ACTIVE' }),
        api.listLocations({ status: 'ACTIVE' }),
        api.listCommercialPartners({ type: 'SUPPLIER', status: 'ACTIVE' }),
      ]);

      setRequests(prRes.data?.items || []);
      setOrders(poRes.data?.items || []);
      setProducts(prodRes.data?.items || []);
      setLocations(locRes.data?.items || []);
      setSuppliers(suppRes.data?.items || []);
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err.message || 'Failed to load procurement data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle PR Creation
  const handleCreatePR = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createPurchaseRequest({
        ...prForm,
        requested_quantity: parseFloat(prForm.requested_quantity),
        estimated_unit_price: prForm.estimated_unit_price ? parseFloat(prForm.estimated_unit_price) : undefined,
      });
      setShowCreatePRModal(false);
      setPrForm({ product_id: '', location_id: '', requested_quantity: '1', estimated_unit_price: '', priority: 'MEDIUM', reason: '' });
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err.message || 'Failed to create purchase request.');
    }
  };

  // Handle PR Approval
  const handleApprovePR = async (prId: string) => {
    try {
      await api.approvePurchaseRequest(prId);
      fetchData();
      if (selectedRequest && selectedRequest.id === prId) {
        const updated = await api.getPurchaseRequest(prId);
        setSelectedRequest(updated.data);
      }
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err.message || 'Failed to approve request.');
    }
  };

  // Handle PR Rejection
  const handleRejectPR = async (prId: string) => {
    const reason = prompt('Please enter a rejection reason:');
    if (reason === null) return;
    try {
      await api.rejectPurchaseRequest(prId, { reason });
      fetchData();
      if (selectedRequest && selectedRequest.id === prId) {
        const updated = await api.getPurchaseRequest(prId);
        setSelectedRequest(updated.data);
      }
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err.message || 'Failed to reject request.');
    }
  };

  // Handle PR to PO Conversion
  const handleConvertPR = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!convertingRequest) return;
    try {
      const res = await api.convertPurchaseRequestToPO(convertingRequest.id, {
        supplier_partner_id: convertForm.supplier_partner_id || undefined,
        expected_delivery_date: convertForm.expected_delivery_date || undefined,
        payment_terms: convertForm.payment_terms,
        unit_price: convertForm.unit_price ? parseFloat(convertForm.unit_price) : undefined,
      });
      setShowConvertModal(false);
      setConvertingRequest(null);
      fetchData();
      setActiveTab('orders');
      setSelectedOrder(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err.message || 'Failed to convert purchase request to PO.');
    }
  };

  // Handle PO Creation
  const handleCreatePO = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createPurchaseOrder({
        ...poForm,
        lines: poForm.lines.map(l => ({
          product_id: l.product_id,
          ordered_quantity: parseFloat(l.ordered_quantity),
          unit_price: parseFloat(l.unit_price),
        })),
      });
      setShowCreatePOModal(false);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err.message || 'Failed to create purchase order.');
    }
  };

  // Handle PO Status Transitions
  const handleApprovePO = async (poId: string) => {
    try {
      await api.approvePurchaseOrder(poId);
      fetchData();
      const updated = await api.getPurchaseOrder(poId);
      setSelectedOrder(updated.data);
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err.message || 'Failed to approve purchase order.');
    }
  };

  const handleSendPO = async (poId: string) => {
    try {
      await api.sendPurchaseOrder(poId);
      fetchData();
      const updated = await api.getPurchaseOrder(poId);
      setSelectedOrder(updated.data);
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err.message || 'Failed to send purchase order.');
    }
  };

  const handleCancelPO = async (poId: string) => {
    const reason = prompt('Please enter a cancellation reason:');
    if (reason === null) return;
    try {
      await api.cancelPurchaseOrder(poId, { reason });
      fetchData();
      const updated = await api.getPurchaseOrder(poId);
      setSelectedOrder(updated.data);
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err.message || 'Failed to cancel purchase order.');
    }
  };

  const filteredOrders = useMemo(() => {
    return orders.filter(po => {
      const matchQuery = !searchQuery || po.po_number.toLowerCase().includes(searchQuery.toLowerCase()) || po.supplier_name?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchStatus = !statusFilter || po.status === statusFilter;
      return matchQuery && matchStatus;
    });
  }, [orders, searchQuery, statusFilter]);

  const filteredRequests = useMemo(() => {
    return requests.filter(pr => {
      const matchQuery = !searchQuery || pr.request_number.toLowerCase().includes(searchQuery.toLowerCase()) || pr.product_name?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchStatus = !statusFilter || pr.status === statusFilter;
      return matchQuery && matchStatus;
    });
  }, [requests, searchQuery, statusFilter]);

  if (loading && orders.length === 0 && requests.length === 0) {
    return <BusinessLoadingState type="table" rows={6} />;
  }

  if (error && orders.length === 0 && requests.length === 0) {
    return <BusinessErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6">
      <OperationsSubNav />

      <BusinessPageHeader
        title="Procurement & Purchase Orders"
        description="Formal supplier purchasing lifecycle, member replenishment requests, and administrative approval gates."
        primaryAction={
          isAdminOrOwner
            ? {
                label: 'New Purchase Order',
                icon: ShoppingCart,
                onClick: () => setShowCreatePOModal(true),
              }
            : undefined
        }
        secondaryActions={[
          {
            label: 'New Purchase Request',
            icon: Plus,
            onClick: () => setShowCreatePRModal(true),
            variant: 'secondary',
          },
        ]}
      />

      {/* Tabs */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-4">
          <button
            onClick={() => { setActiveTab('orders'); setStatusFilter(''); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition cursor-pointer ${
              activeTab === 'orders'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShoppingCart className="w-4 h-4" />
            Purchase Orders ({orders.length})
          </button>
          <button
            onClick={() => { setActiveTab('requests'); setStatusFilter(''); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition cursor-pointer ${
              activeTab === 'requests'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            Purchase Requests ({requests.length})
          </button>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder={`Search ${activeTab === 'orders' ? 'POs' : 'PRs'}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 w-48"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-emerald-500 cursor-pointer"
          >
            <option value="">All Statuses</option>
            {activeTab === 'orders' ? (
              <>
                <option value="DRAFT">DRAFT</option>
                <option value="APPROVED">APPROVED</option>
                <option value="SENT_TO_SUPPLIER">SENT TO SUPPLIER</option>
                <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                <option value="PARTIALLY_RECEIVED">PARTIALLY RECEIVED</option>
                <option value="FULLY_RECEIVED">FULLY RECEIVED</option>
                <option value="CLOSED">CLOSED</option>
                <option value="CANCELLED">CANCELLED</option>
              </>
            ) : (
              <>
                <option value="DRAFT">DRAFT</option>
                <option value="SUBMITTED">SUBMITTED</option>
                <option value="APPROVED">APPROVED</option>
                <option value="ORDERED">ORDERED</option>
                <option value="REJECTED">REJECTED</option>
                <option value="CANCELLED">CANCELLED</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* Main Content Area */}
      {activeTab === 'orders' ? (
        filteredOrders.length === 0 ? (
          <BusinessEmptyState
            title="No Purchase Orders"
            description="Create formal purchase orders to procure stock from approved commercial suppliers."
            actionLabel={isAdminOrOwner ? "Create First Purchase Order" : undefined}
            onAction={isAdminOrOwner ? () => setShowCreatePOModal(true) : undefined}
          />
        ) : (
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden backdrop-blur-md">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/50 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">PO Number</th>
                    <th className="px-4 py-3">Supplier</th>
                    <th className="px-4 py-3">Destination</th>
                    <th className="px-4 py-3">Order Date</th>
                    <th className="px-4 py-3">Expected</th>
                    <th className="px-4 py-3">Total Amount</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredOrders.map((po) => (
                    <tr
                      key={po.id}
                      onClick={() => setSelectedOrder(po)}
                      className="hover:bg-white/[0.02] cursor-pointer transition"
                    >
                      <td className="px-4 py-3 font-semibold text-emerald-400">{po.po_number}</td>
                      <td className="px-4 py-3 font-medium text-slate-200">{po.supplier_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-400">{po.destination_location_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-400">{po.order_date}</td>
                      <td className="px-4 py-3 text-slate-400">{po.expected_delivery_date || '—'}</td>
                      <td className="px-4 py-3 font-semibold text-slate-200">
                        {po.currency} {parseFloat(po.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase ${
                          po.status === 'FULLY_RECEIVED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                          po.status === 'SENT_TO_SUPPLIER' ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30' :
                          po.status === 'APPROVED' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' :
                          po.status === 'DRAFT' ? 'bg-slate-500/20 text-slate-300 border border-slate-500/30' :
                          po.status === 'CANCELLED' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                          'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        }`}>
                          {po.status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => setSelectedOrder(po)}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      ) : (
        filteredRequests.length === 0 ? (
          <BusinessEmptyState
            title="No Purchase Requests"
            description="Staff members can submit replenishment requests for administrative review and approval."
            actionLabel="Submit First Request"
            onAction={() => setShowCreatePRModal(true)}
          />
        ) : (
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden backdrop-blur-md">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/50 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">PR Number</th>
                    <th className="px-4 py-3">Product / SKU</th>
                    <th className="px-4 py-3">Location</th>
                    <th className="px-4 py-3">Qty</th>
                    <th className="px-4 py-3">Est Total</th>
                    <th className="px-4 py-3">Priority</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Requester</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredRequests.map((pr) => (
                    <tr
                      key={pr.id}
                      onClick={() => setSelectedRequest(pr)}
                      className="hover:bg-white/[0.02] cursor-pointer transition"
                    >
                      <td className="px-4 py-3 font-semibold text-emerald-400">{pr.request_number}</td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-200">{pr.product_name}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{pr.product_sku}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-400">{pr.location_name}</td>
                      <td className="px-4 py-3 font-semibold text-slate-200">{pr.requested_quantity}</td>
                      <td className="px-4 py-3 text-slate-300">
                        {pr.currency} {parseFloat(pr.estimated_total_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase ${
                          pr.priority === 'URGENT' ? 'bg-red-500/20 text-red-400' :
                          pr.priority === 'HIGH' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-slate-700/50 text-slate-400'
                        }`}>
                          {pr.priority}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase ${
                          pr.status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                          pr.status === 'ORDERED' ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30' :
                          pr.status === 'SUBMITTED' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                          pr.status === 'REJECTED' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                          'bg-slate-500/20 text-slate-300 border border-slate-500/30'
                        }`}>
                          {pr.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400">{pr.requester_name || 'Staff'}</td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          {isAdminOrOwner && pr.status === 'SUBMITTED' && (
                            <>
                              <button
                                onClick={() => handleApprovePR(pr.id)}
                                title="Approve Request"
                                className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 transition cursor-pointer"
                              >
                                <CheckCircle2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleRejectPR(pr.id)}
                                title="Reject Request"
                                className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition cursor-pointer"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </>
                          )}
                          {isAdminOrOwner && pr.status === 'APPROVED' && (
                            <button
                              onClick={() => {
                                setConvertingRequest(pr);
                                setConvertForm({
                                  supplier_partner_id: '',
                                  expected_delivery_date: '',
                                  payment_terms: 'NET_30',
                                  unit_price: pr.estimated_unit_price,
                                });
                                setShowConvertModal(true);
                              }}
                              className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1 cursor-pointer"
                            >
                              <ShoppingCart className="w-3 h-3" />
                              Create PO
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}

      {/* PO Detail Drawer */}
      {selectedOrder && (
        <DetailDrawer
          isOpen={true}
          onClose={() => setSelectedOrder(null)}
          title={`Purchase Order: ${selectedOrder.po_number}`}
          subtitle={`Issued to ${selectedOrder.supplier_name || 'Supplier'}`}
        >
          <div className="space-y-6 text-xs text-slate-300">
            {/* Header info */}
            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div>
                <div className="text-slate-500 text-[11px]">Supplier</div>
                <div className="font-semibold text-slate-200 mt-0.5">{selectedOrder.supplier_name}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Destination</div>
                <div className="font-semibold text-slate-200 mt-0.5">{selectedOrder.destination_location_name}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Order Date</div>
                <div className="font-medium text-slate-300 mt-0.5">{selectedOrder.order_date}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Expected Delivery</div>
                <div className="font-medium text-slate-300 mt-0.5">{selectedOrder.expected_delivery_date || 'Not specified'}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Payment Terms</div>
                <div className="font-medium text-slate-300 mt-0.5">{selectedOrder.payment_terms}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Status</div>
                <div className="font-semibold text-emerald-400 mt-0.5">{selectedOrder.status.replace(/_/g, ' ')}</div>
              </div>
            </div>

            {/* Line items table */}
            <div>
              <div className="font-semibold text-slate-200 mb-2">Order Line Items</div>
              <div className="rounded-xl border border-slate-800 overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/60 text-slate-400">
                    <tr>
                      <th className="px-3 py-2">Item</th>
                      <th className="px-3 py-2 text-right">Ordered</th>
                      <th className="px-3 py-2 text-right">Received</th>
                      <th className="px-3 py-2 text-right">Unit Price</th>
                      <th className="px-3 py-2 text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {(selectedOrder.lines || []).map((line) => (
                      <tr key={line.id}>
                        <td className="px-3 py-2">
                          <div className="font-medium text-slate-200">{line.product_name}</div>
                          <div className="text-[10px] text-slate-500 font-mono">{line.product_sku}</div>
                        </td>
                        <td className="px-3 py-2 text-right text-slate-200 font-medium">{line.ordered_quantity}</td>
                        <td className="px-3 py-2 text-right text-emerald-400 font-medium">{line.received_quantity}</td>
                        <td className="px-3 py-2 text-right text-slate-400">{line.unit_price}</td>
                        <td className="px-3 py-2 text-right font-semibold text-slate-200">{line.total_price}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Totals */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1.5">
              <div className="flex justify-between text-slate-400">
                <span>Subtotal</span>
                <span>{selectedOrder.currency} {parseFloat(selectedOrder.subtotal_amount).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Tax</span>
                <span>{selectedOrder.currency} {parseFloat(selectedOrder.tax_amount).toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-semibold text-slate-100 text-sm pt-2 border-t border-slate-800">
                <span>Total Amount</span>
                <span className="text-emerald-400">{selectedOrder.currency} {parseFloat(selectedOrder.total_amount).toFixed(2)}</span>
              </div>
            </div>

            {/* Actions for Admin */}
            {isAdminOrOwner && (
              <div className="flex flex-wrap gap-2 pt-2">
                {selectedOrder.status === 'DRAFT' && (
                  <button
                    onClick={() => handleApprovePO(selectedOrder.id)}
                    className="flex-1 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Approve Order
                  </button>
                )}
                {(selectedOrder.status === 'DRAFT' || selectedOrder.status === 'APPROVED') && (
                  <button
                    onClick={() => handleSendPO(selectedOrder.id)}
                    className="flex-1 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <Send className="w-4 h-4" />
                    Send to Supplier
                  </button>
                )}
                {selectedOrder.status !== 'CANCELLED' && selectedOrder.status !== 'FULLY_RECEIVED' && (
                  <button
                    onClick={() => handleCancelPO(selectedOrder.id)}
                    className="py-2 px-4 rounded-xl text-xs font-semibold bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition cursor-pointer"
                  >
                    Cancel Order
                  </button>
                )}
              </div>
            )}
          </div>
        </DetailDrawer>
      )}

      {/* PR Detail Drawer */}
      {selectedRequest && (
        <DetailDrawer
          isOpen={true}
          onClose={() => setSelectedRequest(null)}
          title={`Purchase Request: ${selectedRequest.request_number}`}
          subtitle={`Requested by ${selectedRequest.requester_name || 'Staff'}`}
        >
          <div className="space-y-6 text-xs text-slate-300">
            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div>
                <div className="text-slate-500 text-[11px]">Product</div>
                <div className="font-semibold text-slate-200 mt-0.5">{selectedRequest.product_name}</div>
                <div className="text-[10px] text-slate-500 font-mono">{selectedRequest.product_sku}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Destination Location</div>
                <div className="font-semibold text-slate-200 mt-0.5">{selectedRequest.location_name}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Requested Quantity</div>
                <div className="font-semibold text-slate-200 mt-0.5">{selectedRequest.requested_quantity}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Estimated Total</div>
                <div className="font-semibold text-slate-200 mt-0.5">
                  {selectedRequest.currency} {parseFloat(selectedRequest.estimated_total_price).toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Priority</div>
                <div className="font-semibold text-amber-400 mt-0.5">{selectedRequest.priority}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Status</div>
                <div className="font-semibold text-emerald-400 mt-0.5">{selectedRequest.status}</div>
              </div>
            </div>

            {selectedRequest.reason && (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="text-slate-500 text-[11px]">Business Reason / Justification</div>
                <div className="text-slate-200 mt-1">{selectedRequest.reason}</div>
              </div>
            )}

            {selectedRequest.approval_notes && (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="text-slate-500 text-[11px]">Approval Notes</div>
                <div className="text-slate-200 mt-1">{selectedRequest.approval_notes}</div>
              </div>
            )}

            {isAdminOrOwner && selectedRequest.status === 'SUBMITTED' && (
              <div className="flex gap-3">
                <button
                  onClick={() => handleApprovePR(selectedRequest.id)}
                  className="flex-1 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Approve Request
                </button>
                <button
                  onClick={() => handleRejectPR(selectedRequest.id)}
                  className="flex-1 py-2 rounded-xl text-xs font-semibold bg-red-500/15 hover:bg-red-500/25 text-red-400 border border-red-500/30 transition flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <XCircle className="w-4 h-4" />
                  Reject Request
                </button>
              </div>
            )}
          </div>
        </DetailDrawer>
      )}

      {/* Modal: Create Purchase Request */}
      {showCreatePRModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-slate-100 text-sm">Create Purchase Request</h3>
              <button onClick={() => setShowCreatePRModal(false)} className="text-slate-500 hover:text-slate-300">✕</button>
            </div>
            <form onSubmit={handleCreatePR} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Product to Replenish *</label>
                <select
                  required
                  value={prForm.product_id}
                  onChange={(e) => setPrForm({ ...prForm, product_id: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="">Select a product SKU...</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Destination Location *</label>
                <select
                  required
                  value={prForm.location_id}
                  onChange={(e) => setPrForm({ ...prForm, location_id: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="">Select destination warehouse/store...</option>
                  {locations.map(l => (
                    <option key={l.id} value={l.id}>{l.name} ({l.facility_type})</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Requested Quantity *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={prForm.requested_quantity}
                    onChange={(e) => setPrForm({ ...prForm, requested_quantity: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Priority</label>
                  <select
                    value={prForm.priority}
                    onChange={(e) => setPrForm({ ...prForm, priority: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="URGENT">URGENT</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-slate-400 mb-1">Justification / Operational Reason</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Stock below safety buffer; customer pre-orders waiting"
                  value={prForm.reason}
                  onChange={(e) => setPrForm({ ...prForm, reason: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreatePRModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 font-semibold shadow-sm cursor-pointer"
                >
                  Submit Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Create Purchase Order */}
      {showCreatePOModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-slate-100 text-sm">Create Supplier Purchase Order</h3>
              <button onClick={() => setShowCreatePOModal(false)} className="text-slate-500 hover:text-slate-300">✕</button>
            </div>
            <form onSubmit={handleCreatePO} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Supplier Partner *</label>
                  <select
                    required
                    value={poForm.supplier_partner_id}
                    onChange={(e) => setPoForm({ ...poForm, supplier_partner_id: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">Select a supplier...</option>
                    {suppliers.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Destination Location *</label>
                  <select
                    required
                    value={poForm.destination_location_id}
                    onChange={(e) => setPoForm({ ...poForm, destination_location_id: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">Select receiving facility...</option>
                    {locations.map(l => (
                      <option key={l.id} value={l.id}>{l.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Order Date</label>
                  <input
                    type="date"
                    required
                    value={poForm.order_date}
                    onChange={(e) => setPoForm({ ...poForm, order_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Expected Delivery Date</label>
                  <input
                    type="date"
                    value={poForm.expected_delivery_date}
                    onChange={(e) => setPoForm({ ...poForm, expected_delivery_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* Line Items */}
              <div className="space-y-2 pt-2 border-t border-slate-800">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-slate-300">Line Items</span>
                  <button
                    type="button"
                    onClick={() => setPoForm({
                      ...poForm,
                      lines: [...poForm.lines, { product_id: '', ordered_quantity: '1', unit_price: '0.00' }]
                    })}
                    className="text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Item
                  </button>
                </div>

                {poForm.lines.map((line, idx) => (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-center bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                    <div className="col-span-6">
                      <select
                        required
                        value={line.product_id}
                        onChange={(e) => {
                          const updated = [...poForm.lines];
                          const selectedProd = products.find(p => p.id === e.target.value);
                          updated[idx].product_id = e.target.value;
                          if (selectedProd) updated[idx].unit_price = selectedProd.cost_price || '0.00';
                          setPoForm({ ...poForm, lines: updated });
                        }}
                        className="w-full px-2 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs"
                      >
                        <option value="">Select product...</option>
                        {products.map(p => (
                          <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                        ))}
                      </select>
                    </div>
                    <div className="col-span-3">
                      <input
                        type="number"
                        step="0.01"
                        min="0.01"
                        required
                        placeholder="Qty"
                        value={line.ordered_quantity}
                        onChange={(e) => {
                          const updated = [...poForm.lines];
                          updated[idx].ordered_quantity = e.target.value;
                          setPoForm({ ...poForm, lines: updated });
                        }}
                        className="w-full px-2 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs text-right"
                      />
                    </div>
                    <div className="col-span-2">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        required
                        placeholder="Price"
                        value={line.unit_price}
                        onChange={(e) => {
                          const updated = [...poForm.lines];
                          updated[idx].unit_price = e.target.value;
                          setPoForm({ ...poForm, lines: updated });
                        }}
                        className="w-full px-2 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-xs text-right"
                      />
                    </div>
                    <div className="col-span-1 text-center">
                      {poForm.lines.length > 1 && (
                        <button
                          type="button"
                          onClick={() => {
                            const updated = poForm.lines.filter((_, i) => i !== idx);
                            setPoForm({ ...poForm, lines: updated });
                          }}
                          className="text-red-400 hover:text-red-300 cursor-pointer"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreatePOModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 font-semibold shadow-sm cursor-pointer"
                >
                  Create Purchase Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Convert PR to PO */}
      {showConvertModal && convertingRequest && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-slate-100 text-sm">Convert PR to Purchase Order</h3>
              <button onClick={() => setShowConvertModal(false)} className="text-slate-500 hover:text-slate-300">✕</button>
            </div>
            <form onSubmit={handleConvertPR} className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 space-y-1">
                <div><span className="text-slate-500">Request:</span> {convertingRequest.request_number}</div>
                <div><span className="text-slate-500">Item:</span> {convertingRequest.product_name}</div>
                <div><span className="text-slate-500">Quantity:</span> {convertingRequest.requested_quantity} units</div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Supplier Partner *</label>
                <select
                  required
                  value={convertForm.supplier_partner_id}
                  onChange={(e) => setConvertForm({ ...convertForm, supplier_partner_id: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="">Select supplier...</option>
                  {suppliers.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Unit Price</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={convertForm.unit_price}
                    onChange={(e) => setConvertForm({ ...convertForm, unit_price: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Payment Terms</label>
                  <select
                    value={convertForm.payment_terms}
                    onChange={(e) => setConvertForm({ ...convertForm, payment_terms: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="NET_30">NET_30</option>
                    <option value="NET_15">NET_15</option>
                    <option value="DUE_ON_RECEIPT">DUE_ON_RECEIPT</option>
                    <option value="ADVANCE">ADVANCE</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Expected Delivery Date</label>
                <input
                  type="date"
                  value={convertForm.expected_delivery_date}
                  onChange={(e) => setConvertForm({ ...convertForm, expected_delivery_date: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowConvertModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 font-semibold shadow-sm cursor-pointer"
                >
                  Generate PO
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
