import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ShoppingCart,
  Plus,
  Search,
  FileText,
  CheckCircle2,
  XCircle,
  Send,
  Truck,
  PackageCheck,
  Receipt,
  FileCheck,
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

interface GoodsReceiptLine {
  id: string;
  goods_receipt_id: string;
  purchase_order_line_id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  product_unit?: string;
  received_quantity: string;
  accepted_quantity: string;
  rejected_quantity: string;
  rejection_reason?: string;
  unit_cost: string;
  stock_movement_id?: string;
  created_at: string;
}

interface GoodsReceipt {
  id: string;
  grn_number: string;
  purchase_order_id: string;
  po_number: string;
  supplier_partner_id: string;
  supplier_name: string;
  destination_location_id: string;
  destination_location_name: string;
  receipt_date: string;
  carrier_name?: string;
  tracking_number?: string;
  delivery_note_number?: string;
  status: string;
  notes?: string;
  staged_extraction_id?: string;
  received_by_user_id?: string;
  receiver_name?: string;
  created_at: string;
  lines?: GoodsReceiptLine[];
}

export const BusinessProcurement: React.FC = () => {
  const { role } = useBusinessAuth();
  const [activeTab, setActiveTab] = useState<'orders' | 'requests' | 'grns'>('orders');

  // Data states
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [requests, setRequests] = useState<PurchaseRequest[]>([]);
  const [grns, setGrns] = useState<GoodsReceipt[]>([]);
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
  const [selectedGrn, setSelectedGrn] = useState<GoodsReceipt | null>(null);
  const [showCreatePRModal, setShowCreatePRModal] = useState(false);
  const [showCreatePOModal, setShowCreatePOModal] = useState(false);
  const [showConvertModal, setShowConvertModal] = useState(false);
  const [convertingRequest, setConvertingRequest] = useState<PurchaseRequest | null>(null);
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [receivingOrder, setReceivingOrder] = useState<PurchaseOrder | null>(null);

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

  const [receiveForm, setReceiveForm] = useState<{
    receipt_date: string;
    carrier_name: string;
    tracking_number: string;
    delivery_note_number: string;
    notes: string;
    lines: Array<{
      purchase_order_line_id: string;
      product_id: string;
      product_name: string;
      product_sku: string;
      ordered_quantity: string;
      previously_received: string;
      received_quantity: string;
      accepted_quantity: string;
      rejected_quantity: string;
      rejection_reason: string;
    }>;
  }>({
    receipt_date: new Date().toISOString().split('T')[0],
    carrier_name: '',
    tracking_number: '',
    delivery_note_number: '',
    notes: '',
    lines: [],
  });

  const isAdminOrOwner = role === 'OWNER' || role === 'ADMIN';
  const canReceive = role === 'OWNER' || role === 'ADMIN' || role === 'MEMBER';

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [prRes, poRes, grnRes, prodRes, locRes, suppRes] = await Promise.all([
        api.listPurchaseRequests(),
        api.listPurchaseOrders(),
        api.listGoodsReceipts(),
        api.listProducts({ status: 'ACTIVE' }),
        api.listLocations({ status: 'ACTIVE' }),
        api.listCommercialPartners({ type: 'SUPPLIER', status: 'ACTIVE' }),
      ]);

      setRequests(prRes.data?.items || []);
      setOrders(poRes.data?.items || []);
      setGrns(grnRes.data?.items || []);
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

  // Handle Goods Receipt (GRN) Opening
  const openReceiveModal = (po: PurchaseOrder) => {
    setReceivingOrder(po);
    const initialLines = (po.lines || []).map(line => {
      const remaining = Math.max(0, parseFloat(line.ordered_quantity) - parseFloat(line.received_quantity));
      return {
        purchase_order_line_id: line.id,
        product_id: line.product_id,
        product_name: line.product_name,
        product_sku: line.product_sku,
        ordered_quantity: line.ordered_quantity,
        previously_received: line.received_quantity,
        received_quantity: remaining.toString(),
        accepted_quantity: remaining.toString(),
        rejected_quantity: '0',
        rejection_reason: '',
      };
    });

    setReceiveForm({
      receipt_date: new Date().toISOString().split('T')[0],
      carrier_name: '',
      tracking_number: '',
      delivery_note_number: '',
      notes: '',
      lines: initialLines,
    });
    setShowReceiveModal(true);
  };

  // Handle Goods Receipt (GRN) Submission
  const handleCreateGRN = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!receivingOrder) return;
    try {
      const payload = {
        purchase_order_id: receivingOrder.id,
        receipt_date: receiveForm.receipt_date || undefined,
        carrier_name: receiveForm.carrier_name || undefined,
        tracking_number: receiveForm.tracking_number || undefined,
        delivery_note_number: receiveForm.delivery_note_number || undefined,
        notes: receiveForm.notes || undefined,
        lines: receiveForm.lines.map(l => ({
          purchase_order_line_id: l.purchase_order_line_id,
          received_quantity: parseFloat(l.received_quantity || '0'),
          accepted_quantity: parseFloat(l.accepted_quantity || '0'),
          rejected_quantity: parseFloat(l.rejected_quantity || '0'),
          rejection_reason: l.rejection_reason || undefined,
        })),
      };

      const res = await api.createGoodsReceipt(payload);
      setShowReceiveModal(false);
      setReceivingOrder(null);
      fetchData();
      setActiveTab('grns');
      setSelectedGrn(res.data);
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err.message || 'Failed to record goods receipt.');
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

  const filteredGrns = useMemo(() => {
    return grns.filter(grn => {
      const matchQuery = !searchQuery || grn.grn_number.toLowerCase().includes(searchQuery.toLowerCase()) || grn.po_number?.toLowerCase().includes(searchQuery.toLowerCase()) || grn.supplier_name?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchStatus = !statusFilter || grn.status === statusFilter;
      return matchQuery && matchStatus;
    });
  }, [grns, searchQuery, statusFilter]);

  if (loading && orders.length === 0 && requests.length === 0 && grns.length === 0) {
    return <BusinessLoadingState type="table" rows={6} />;
  }

  if (error && orders.length === 0 && requests.length === 0 && grns.length === 0) {
    return <BusinessErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <div className="space-y-6">
      <OperationsSubNav />

      <BusinessPageHeader
        title="Procurement & Receiving"
        description="Formal supplier purchasing lifecycle, goods receipt notes (GRN), and staging-gated Accounts Payable proposals."
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
            onClick={() => { setActiveTab('grns'); setStatusFilter(''); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition cursor-pointer ${
              activeTab === 'grns'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Truck className="w-4 h-4" />
            Goods Receipts / GRNs ({grns.length})
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
              placeholder={`Search ${activeTab === 'orders' ? 'POs' : activeTab === 'grns' ? 'GRNs' : 'PRs'}...`}
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
            {activeTab === 'orders' && (
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
            )}
            {activeTab === 'grns' && (
              <>
                <option value="COMPLETED">COMPLETED</option>
                <option value="CANCELLED">CANCELLED</option>
              </>
            )}
            {activeTab === 'requests' && (
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
      {activeTab === 'orders' && (
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
                          po.status === 'PARTIALLY_RECEIVED' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                          po.status === 'SENT_TO_SUPPLIER' ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30' :
                          po.status === 'APPROVED' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' :
                          po.status === 'DRAFT' ? 'bg-slate-500/20 text-slate-300 border border-slate-500/30' :
                          po.status === 'CANCELLED' ? 'bg-red-500/20 text-red-300 border border-red-500/30' :
                          'bg-slate-700/50 text-slate-300'
                        }`}>
                          {po.status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          {canReceive && (po.status === 'SENT_TO_SUPPLIER' || po.status === 'APPROVED' || po.status === 'ACKNOWLEDGED' || po.status === 'PARTIALLY_RECEIVED') && (
                            <button
                              onClick={() => openReceiveModal(po)}
                              className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1 cursor-pointer"
                            >
                              <Truck className="w-3 h-3" />
                              Receive
                            </button>
                          )}
                          <button
                            onClick={() => setSelectedOrder(po)}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
                          >
                            View
                          </button>
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

      {/* Goods Receipts (GRNs) Tab */}
      {activeTab === 'grns' && (
        filteredGrns.length === 0 ? (
          <BusinessEmptyState
            title="No Goods Receipts Recorded"
            description="When physical goods arrive from suppliers against active Purchase Orders, record a GRN to inspect and bridge stock into inventory."
          />
        ) : (
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden backdrop-blur-md">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/50 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">GRN Number</th>
                    <th className="px-4 py-3">Originating PO</th>
                    <th className="px-4 py-3">Supplier</th>
                    <th className="px-4 py-3">Facility</th>
                    <th className="px-4 py-3">Receipt Date</th>
                    <th className="px-4 py-3">Carrier / Note #</th>
                    <th className="px-4 py-3">AP Staging</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredGrns.map((grn) => (
                    <tr
                      key={grn.id}
                      onClick={() => setSelectedGrn(grn)}
                      className="hover:bg-white/[0.02] cursor-pointer transition"
                    >
                      <td className="px-4 py-3 font-semibold text-emerald-400 flex items-center gap-1.5">
                        <PackageCheck className="w-3.5 h-3.5 text-emerald-500" />
                        {grn.grn_number}
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-200">{grn.po_number || '—'}</td>
                      <td className="px-4 py-3 text-slate-300">{grn.supplier_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-400">{grn.destination_location_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-400">{grn.receipt_date}</td>
                      <td className="px-4 py-3 text-slate-400">
                        {grn.delivery_note_number || grn.carrier_name || '—'}
                      </td>
                      <td className="px-4 py-3">
                        {grn.staged_extraction_id ? (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1 w-fit">
                            <Receipt className="w-3 h-3" />
                            AP Staged
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[10px]">None</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => setSelectedGrn(grn)}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
                        >
                          View GRN
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}

      {/* Purchase Requests Tab */}
      {activeTab === 'requests' && (
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

            {/* Actions for Receiving / Managing */}
            <div className="space-y-2 pt-2">
              {canReceive && (selectedOrder.status === 'SENT_TO_SUPPLIER' || selectedOrder.status === 'APPROVED' || selectedOrder.status === 'ACKNOWLEDGED' || selectedOrder.status === 'PARTIALLY_RECEIVED') && (
                <button
                  onClick={() => {
                    const po = selectedOrder;
                    setSelectedOrder(null);
                    openReceiveModal(po);
                  }}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center justify-center gap-1.5 shadow-md cursor-pointer"
                >
                  <Truck className="w-4 h-4" />
                  Receive Goods / Issue GRN
                </button>
              )}

              {isAdminOrOwner && (
                <div className="flex flex-wrap gap-2">
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
                      className="flex-1 py-2 rounded-xl text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white transition flex items-center justify-center gap-1.5 cursor-pointer"
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
          </div>
        </DetailDrawer>
      )}

      {/* GRN Detail Drawer */}
      {selectedGrn && (
        <DetailDrawer
          isOpen={true}
          onClose={() => setSelectedGrn(null)}
          title={`Goods Receipt Note: ${selectedGrn.grn_number}`}
          subtitle={`Delivered against PO: ${selectedGrn.po_number || selectedGrn.purchase_order_id}`}
        >
          <div className="space-y-6 text-xs text-slate-300">
            <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div>
                <div className="text-slate-500 text-[11px]">Supplier</div>
                <div className="font-semibold text-slate-200 mt-0.5">{selectedGrn.supplier_name}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Receiving Facility</div>
                <div className="font-semibold text-slate-200 mt-0.5">{selectedGrn.destination_location_name}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Receipt Date</div>
                <div className="font-medium text-slate-300 mt-0.5">{selectedGrn.receipt_date}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Receiver (Staff)</div>
                <div className="font-medium text-slate-300 mt-0.5">{selectedGrn.receiver_name || 'Staff Member'}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Carrier / Tracking</div>
                <div className="font-medium text-slate-300 mt-0.5">{selectedGrn.carrier_name || selectedGrn.tracking_number || 'Direct Delivery'}</div>
              </div>
              <div>
                <div className="text-slate-500 text-[11px]">Delivery Note #</div>
                <div className="font-medium text-slate-300 mt-0.5">{selectedGrn.delivery_note_number || 'None'}</div>
              </div>
            </div>

            {/* AP Staging Status Banner */}
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
              <Receipt className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-amber-300">Accounts Payable Staging Candidate</div>
                <div className="text-slate-300 text-[11px] mt-0.5">
                  Physical stock has been accepted into inventory. A corresponding Accounts Payable invoice proposal is queued in Staging awaiting review.
                </div>
              </div>
            </div>

            {/* Inspected Line Items */}
            <div>
              <div className="font-semibold text-slate-200 mb-2">Delivered & Inspected Lines</div>
              <div className="rounded-xl border border-slate-800 overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/60 text-slate-400">
                    <tr>
                      <th className="px-3 py-2">Item</th>
                      <th className="px-3 py-2 text-right">Received</th>
                      <th className="px-3 py-2 text-right text-emerald-400">Accepted</th>
                      <th className="px-3 py-2 text-right text-red-400">Rejected</th>
                      <th className="px-3 py-2 text-right">Unit Cost</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {(selectedGrn.lines || []).map((line) => (
                      <tr key={line.id}>
                        <td className="px-3 py-2">
                          <div className="font-medium text-slate-200">{line.product_name}</div>
                          <div className="text-[10px] text-slate-500 font-mono">{line.product_sku}</div>
                          {line.rejection_reason && (
                            <div className="text-[10px] text-red-400 mt-0.5 italic">Reason: {line.rejection_reason}</div>
                          )}
                        </td>
                        <td className="px-3 py-2 text-right text-slate-300">{line.received_quantity}</td>
                        <td className="px-3 py-2 text-right text-emerald-400 font-semibold">{line.accepted_quantity}</td>
                        <td className="px-3 py-2 text-right text-red-400 font-medium">{line.rejected_quantity}</td>
                        <td className="px-3 py-2 text-right text-slate-300">₹{line.unit_cost}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {selectedGrn.notes && (
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="text-slate-500 text-[11px]">Receiving Inspection Notes</div>
                <div className="text-slate-200 mt-1">{selectedGrn.notes}</div>
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

      {/* Modal: Create Goods Receipt Note (GRN) */}
      {showReceiveModal && receivingOrder && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold text-slate-100 text-sm flex items-center gap-2">
                  <Truck className="w-4 h-4 text-emerald-400" />
                  Receive Goods / Issue GRN
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">PO: {receivingOrder.po_number} · Supplier: {receivingOrder.supplier_name}</p>
              </div>
              <button onClick={() => setShowReceiveModal(false)} className="text-slate-500 hover:text-slate-300">✕</button>
            </div>

            <form onSubmit={handleCreateGRN} className="space-y-4 text-xs">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Receipt Date *</label>
                  <input
                    type="date"
                    required
                    value={receiveForm.receipt_date}
                    onChange={(e) => setReceiveForm({ ...receiveForm, receipt_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Delivery Slip / Note #</label>
                  <input
                    type="text"
                    placeholder="e.g. DN-98421"
                    value={receiveForm.delivery_note_number}
                    onChange={(e) => setReceiveForm({ ...receiveForm, delivery_note_number: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Carrier / Tracking</label>
                  <input
                    type="text"
                    placeholder="e.g. BlueDart #8492"
                    value={receiveForm.carrier_name}
                    onChange={(e) => setReceiveForm({ ...receiveForm, carrier_name: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* Line items inspection */}
              <div className="space-y-3 pt-2 border-t border-slate-800">
                <span className="font-semibold text-slate-300 block">Item Inspection & Quantities</span>

                {receiveForm.lines.map((line, idx) => (
                  <div key={line.purchase_order_line_id} className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-semibold text-slate-200">{line.product_name}</span>
                        <span className="text-[10px] text-slate-500 font-mono ml-2">{line.product_sku}</span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        Ordered: <span className="font-medium text-slate-200">{line.ordered_quantity}</span> | Previously Received: <span className="font-medium text-slate-200">{line.previously_received}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <label className="block text-[11px] text-slate-400 mb-1">Total Delivered Qty *</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          required
                          value={line.received_quantity}
                          onChange={(e) => {
                            const updated = [...receiveForm.lines];
                            const val = e.target.value;
                            updated[idx].received_quantity = val;
                            // Default accepted quantity to received quantity
                            updated[idx].accepted_quantity = val;
                            updated[idx].rejected_quantity = '0';
                            setReceiveForm({ ...receiveForm, lines: updated });
                          }}
                          className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-right font-medium"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] text-emerald-400 mb-1">Accepted Qty (Stocked) *</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          required
                          value={line.accepted_quantity}
                          onChange={(e) => {
                            const updated = [...receiveForm.lines];
                            const accVal = parseFloat(e.target.value || '0');
                            const recvVal = parseFloat(updated[idx].received_quantity || '0');
                            updated[idx].accepted_quantity = e.target.value;
                            updated[idx].rejected_quantity = Math.max(0, recvVal - accVal).toString();
                            setReceiveForm({ ...receiveForm, lines: updated });
                          }}
                          className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-emerald-500/40 text-emerald-300 text-right font-medium"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] text-red-400 mb-1">Rejected / Damaged Qty</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={line.rejected_quantity}
                          onChange={(e) => {
                            const updated = [...receiveForm.lines];
                            const rejVal = parseFloat(e.target.value || '0');
                            const recvVal = parseFloat(updated[idx].received_quantity || '0');
                            updated[idx].rejected_quantity = e.target.value;
                            updated[idx].accepted_quantity = Math.max(0, recvVal - rejVal).toString();
                            setReceiveForm({ ...receiveForm, lines: updated });
                          }}
                          className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-red-500/40 text-red-300 text-right font-medium"
                        />
                      </div>
                    </div>

                    {parseFloat(line.rejected_quantity || '0') > 0 && (
                      <div>
                        <label className="block text-[10px] text-red-400 mb-0.5">Rejection / Damage Reason</label>
                        <input
                          type="text"
                          placeholder="e.g. Broken packaging, wrong specifications"
                          value={line.rejection_reason}
                          onChange={(e) => {
                            const updated = [...receiveForm.lines];
                            updated[idx].rejection_reason = e.target.value;
                            setReceiveForm({ ...receiveForm, lines: updated });
                          }}
                          className="w-full px-2.5 py-1 rounded-lg bg-slate-900 border border-red-500/30 text-slate-200 text-xs"
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div>
                <label className="block text-slate-400 mb-1">General Receiving Notes</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Inspected at Loading Bay 3; quality seal verified"
                  value={receiveForm.notes}
                  onChange={(e) => setReceiveForm({ ...receiveForm, notes: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowReceiveModal(false)}
                  className="flex-1 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-500 font-semibold shadow-sm flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <FileCheck className="w-4 h-4" />
                  Complete Receiving & Issue GRN
                </button>
              </div>
            </form>
          </div>
        </div>
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
