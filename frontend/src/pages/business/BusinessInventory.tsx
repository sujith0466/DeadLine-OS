import React, { useState, useEffect, useCallback } from 'react';
import {
  Package,
  Plus,
  ArrowLeftRight,
  History,
  AlertTriangle,
  MapPin,
  Search,
  TrendingDown,
  Building2,
} from 'lucide-react';
import { api } from '../../api';
import { useBusinessAuth } from '../../context/BusinessAuthContext';
import { BusinessPageHeader } from '../../components/Business/BusinessPageHeader';
import { OperationsSubNav } from '../../components/Business/OperationsSubNav';
import { BusinessDataTable } from '../../components/Business/BusinessDataTable';
import type { ColumnDef } from '../../components/Business/BusinessDataTable';
import { DetailDrawer } from '../../components/Business/DetailDrawer';
import { StatusBadge } from '../../components/Business/StatusBadge';

export interface InventoryStockItem extends Record<string, any> {
  product_id: string;
  sku: string;
  name: string;
  category?: string | null;
  unit: string;
  current_quantity: string;
  reorder_level: string;
  safety_stock: string;
  cost_price: string;
  selling_price: string;
  stock_value: string;
  currency: string;
  status: 'HEALTHY' | 'LOW' | 'OUT_OF_STOCK';
  is_critical_safety: boolean;
  preferred_supplier_partner_id?: string | null;
  supplier_name?: string | null;
  location_breakdown: Array<{
    location_id: string;
    location_name: string;
    quantity: string;
  }>;
}

export interface StockMovementItem {
  id: string;
  product_id: string;
  product_name?: string | null;
  product_sku?: string | null;
  location_id: string;
  location_name?: string | null;
  movement_type: string;
  direction: 'IN' | 'OUT';
  quantity: string;
  unit_cost?: string | null;
  reference_type?: string | null;
  reference_id?: string | null;
  transfer_batch_id?: string | null;
  actor_name?: string | null;
  reason?: string | null;
  created_at: string;
}

export const BusinessInventory: React.FC = () => {
  const { activeWorkspace, role } = useBusinessAuth();

  const [inventoryData, setInventoryData] = useState<any>({
    total_skus: 0,
    low_stock_count: 0,
    out_of_stock_count: 0,
    total_stock_valuation: '0.00',
    currency: 'INR',
    items: [],
  });
  const [locations, setLocations] = useState<any[]>([]);
  const [partners, setPartners] = useState<any[]>([]);
  const [movements, setMovements] = useState<StockMovementItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [selectedLocationId, setSelectedLocationId] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals & Drawers
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [isMovementModalOpen, setIsMovementModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<InventoryStockItem | null>(null);
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState(false);

  // Form States
  // 1. Create Product Form
  const [prodSku, setProdSku] = useState('');
  const [prodName, setProdName] = useState('');
  const [prodCategory, setProdCategory] = useState('');
  const [prodUnit, setProdUnit] = useState('UNIT');
  const [prodReorder, setProdReorder] = useState('10.00');
  const [prodSafety, setProdSafety] = useState('5.00');
  const [prodCost, setProdCost] = useState('0.00');
  const [prodSelling, setProdSelling] = useState('0.00');
  const [prodSupplierId, setProdSupplierId] = useState('');

  // 2. Create Location Form
  const [locName, setLocName] = useState('');
  const [locType, setLocType] = useState('WAREHOUSE');
  const [locAddress, setLocAddress] = useState('');

  // 3. Movement Form
  const [movProductId, setMovProductId] = useState('');
  const [movLocationId, setMovLocationId] = useState('');
  const [movType, setMovType] = useState('MANUAL_ADJUSTMENT');
  const [movDirection, setMovDirection] = useState('IN');
  const [movQuantity, setMovQuantity] = useState('1.00');
  const [movUnitCost, setMovUnitCost] = useState('');
  const [movReason, setMovReason] = useState('');

  // 4. Transfer Form
  const [trfProductId, setTrfProductId] = useState('');
  const [trfSourceLocId, setTrfSourceLocId] = useState('');
  const [trfDestLocId, setTrfDestLocId] = useState('');
  const [trfQuantity, setTrfQuantity] = useState('1.00');
  const [trfReason, setTrfReason] = useState('');

  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canManage = role === 'OWNER' || role === 'ADMIN' || role === 'MEMBER';

  const fetchData = useCallback(async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const locParam = selectedLocationId === 'ALL' ? undefined : selectedLocationId;
      const statusParam = statusFilter === 'ALL' ? undefined : statusFilter;

      const [invRes, locsRes, partnersRes] = await Promise.allSettled([
        api.getInventory({ location_id: locParam, status: statusParam, search: searchQuery || undefined }),
        api.listLocations(),
        api.listCommercialPartners({ type: 'SUPPLIER' }),
      ]);

      if (invRes.status === 'fulfilled' && invRes.value?.data) {
        setInventoryData(invRes.value.data);
      }
      if (locsRes.status === 'fulfilled' && locsRes.value?.data?.locations) {
        setLocations(locsRes.value.data.locations);
      }
      if (partnersRes.status === 'fulfilled' && partnersRes.value?.data?.partners) {
        setPartners(partnersRes.value.data.partners);
      }
    } catch (err: any) {
      console.error('Failed to load inventory data', err);
    } finally {
      setLoading(false);
    }
  }, [activeWorkspace, selectedLocationId, statusFilter, searchQuery]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const fetchMovements = async (productId?: string) => {
    try {
      const res = await api.listStockMovements({ product_id: productId });
      if (res?.data?.movements) {
        setMovements(res.data.movements);
      }
    } catch (err: any) {
      console.error('Failed to load movements', err);
    }
  };

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prodSku.trim() || !prodName.trim()) {
      setFormError('SKU and Product Name are required.');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);
    try {
      await api.createProduct({
        sku: prodSku.trim().toUpperCase(),
        name: prodName.trim(),
        category: prodCategory.trim() || undefined,
        unit: prodUnit,
        reorder_level: prodReorder,
        safety_stock: prodSafety,
        cost_price: prodCost,
        selling_price: prodSelling,
        preferred_supplier_partner_id: prodSupplierId || undefined,
      });
      setIsProductModalOpen(false);
      // Reset
      setProdSku('');
      setProdName('');
      setProdCategory('');
      setProdUnit('UNIT');
      setProdReorder('10.00');
      setProdSafety('5.00');
      setProdCost('0.00');
      setProdSelling('0.00');
      setProdSupplierId('');
      fetchData();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create product.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateLocation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!locName.trim()) {
      setFormError('Location Name is required.');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);
    try {
      await api.createLocation({
        name: locName.trim(),
        location_type: locType,
        address: locAddress.trim() || undefined,
      });
      setIsLocationModalOpen(false);
      setLocName('');
      setLocType('WAREHOUSE');
      setLocAddress('');
      fetchData();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to create location.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRecordMovement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!movProductId || !movLocationId) {
      setFormError('Product and Location are required.');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);
    try {
      await api.recordStockMovement({
        product_id: movProductId,
        location_id: movLocationId,
        movement_type: movType,
        direction: movDirection,
        quantity: movQuantity,
        unit_cost: movUnitCost ? movUnitCost : undefined,
        reason: movReason.trim() || undefined,
      });
      setIsMovementModalOpen(false);
      setMovQuantity('1.00');
      setMovReason('');
      setMovUnitCost('');
      fetchData();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to record stock movement.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trfProductId || !trfSourceLocId || !trfDestLocId) {
      setFormError('Product, Source, and Destination locations are required.');
      return;
    }
    if (trfSourceLocId === trfDestLocId) {
      setFormError('Source and Destination locations must be different.');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);
    try {
      await api.transferStock({
        product_id: trfProductId,
        source_location_id: trfSourceLocId,
        destination_location_id: trfDestLocId,
        quantity: trfQuantity,
        reason: trfReason.trim() || undefined,
      });
      setIsTransferModalOpen(false);
      setTrfQuantity('1.00');
      setTrfReason('');
      fetchData();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to execute stock transfer.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: ColumnDef<InventoryStockItem>[] = [
    {
      key: 'sku',
      header: 'SKU & Product Name',
      render: (item: InventoryStockItem) => (
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="font-mono font-bold text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
              {item.sku}
            </span>
            <span className="font-semibold text-slate-100">{item.name}</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
            {item.category && (
              <span className="bg-slate-800 px-1.5 py-0.5 rounded text-[10px] uppercase font-mono">{item.category}</span>
            )}
            <span className="text-slate-500">Unit: {item.unit}</span>
            {item.supplier_name && (
              <span className="text-slate-400">Supplier: {item.supplier_name}</span>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'current_quantity',
      header: 'Derived Current Stock',
      render: (item: InventoryStockItem) => {
        const qty = parseFloat(item.current_quantity);
        return (
          <div className="flex flex-col">
            <span className={`text-base font-bold font-mono ${qty <= 0 ? 'text-rose-400' : 'text-slate-100'}`}>
              {item.current_quantity} <span className="text-xs text-slate-400 font-normal">{item.unit}</span>
            </span>
            <span className="text-[11px] text-slate-400 mt-0.5">
              Reorder: {item.reorder_level} | Safety: {item.safety_stock}
            </span>
          </div>
        );
      },
    },
    {
      key: 'stock_value',
      header: 'Valuation (Cost Basis)',
      render: (item: InventoryStockItem) => (
        <div className="flex flex-col">
          <span className="font-mono text-xs font-semibold text-slate-200">
            ₹{parseFloat(item.stock_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
          <span className="text-[10px] text-slate-500">@ ₹{item.cost_price}/{item.unit}</span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Stock Status',
      render: (item: InventoryStockItem) => {
        if (item.status === 'OUT_OF_STOCK') {
          return <StatusBadge status="OUT_OF_STOCK" />;
        }
        if (item.is_critical_safety) {
          return (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse flex items-center gap-1 w-fit">
              <AlertTriangle className="w-3 h-3 text-rose-400" />
              CRITICAL SAFETY
            </span>
          );
        }
        if (item.status === 'LOW') {
          return <StatusBadge status="LOW" />;
        }
        return <StatusBadge status="ACTIVE" />;
      },
    },
    {
      key: 'locations',
      header: 'Location Breakdown',
      render: (item: InventoryStockItem) => (
        <div className="flex flex-wrap gap-1 max-w-xs">
          {item.location_breakdown.length === 0 ? (
            <span className="text-xs text-slate-500 italic">No recorded locations</span>
          ) : (
            item.location_breakdown.map((loc) => (
              <span
                key={loc.location_id}
                className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1"
              >
                <MapPin className="w-2.5 h-2.5 text-slate-400" />
                {loc.location_name}: <strong className="text-slate-100">{loc.quantity}</strong>
              </span>
            ))
          )}
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (item: InventoryStockItem) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setSelectedItem(item);
            setIsDetailDrawerOpen(true);
            fetchMovements(item.product_id);
          }}
          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
        >
          Ledger
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <BusinessPageHeader
        title="Inventory & Stock Management"
        description="Immutable stock movement ledger, live derived quantities, and low-stock monitoring."
        primaryAction={
          canManage
            ? {
                label: 'New SKU',
                onClick: () => setIsProductModalOpen(true),
                icon: Plus,
                variant: 'primary',
              }
            : undefined
        }
        secondaryActions={
          canManage
            ? [
                {
                  label: 'Add Facility',
                  onClick: () => setIsLocationModalOpen(true),
                  icon: Building2,
                  variant: 'secondary',
                },
                {
                  label: 'Transfer Stock',
                  onClick: () => {
                    setIsTransferModalOpen(true);
                    if (inventoryData.items.length > 0 && !trfProductId) {
                      setTrfProductId(inventoryData.items[0].product_id);
                    }
                  },
                  icon: ArrowLeftRight,
                  variant: 'secondary',
                },
                {
                  label: 'Record Movement',
                  onClick: () => {
                    setIsMovementModalOpen(true);
                    if (inventoryData.items.length > 0 && !movProductId) {
                      setMovProductId(inventoryData.items[0].product_id);
                    }
                  },
                  icon: TrendingDown,
                  variant: 'secondary',
                },
              ]
            : undefined
        }
      />

      <OperationsSubNav />

      {/* Metrics Header */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Catalog SKUs</span>
          <div className="text-xl font-bold text-slate-100 mt-1">{inventoryData.total_skus}</div>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Stock Value</span>
          <div className="text-xl font-bold text-emerald-400 mt-1">
            ₹{parseFloat(inventoryData.total_stock_valuation || '0').toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </div>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-amber-500/30 bg-amber-500/5 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">Low Stock Alerts</span>
          <div className="text-xl font-bold text-amber-400 mt-1">{inventoryData.low_stock_count}</div>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-rose-500/30 bg-rose-500/5 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider">Out of Stock</span>
          <div className="text-xl font-bold text-rose-400 mt-1">{inventoryData.out_of_stock_count}</div>
        </div>
        <div className="p-3.5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Active Facilities</span>
          <div className="text-xl font-bold text-slate-300 mt-1">{locations.length}</div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 p-2 rounded-2xl bg-slate-900/60 border border-slate-800/80">
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar w-full md:w-auto">
          {[
            { id: 'ALL', label: 'All Stock' },
            { id: 'LOW', label: 'Low Stock Only' },
            { id: 'OUT_OF_STOCK', label: 'Out of Stock' },
            { id: 'HEALTHY', label: 'Healthy Stock' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                statusFilter === tab.id
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <select
            value={selectedLocationId}
            onChange={(e) => setSelectedLocationId(e.target.value)}
            className="bg-slate-950/80 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500/50"
          >
            <option value="ALL">All Facilities</option>
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>

          <div className="relative flex-1 md:w-56">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search SKU or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
          </div>
        </div>
      </div>

      {/* Main Table */}
      <BusinessDataTable
        data={inventoryData.items}
        columns={columns}
        keyExtractor={(item) => item.product_id}
        loading={loading}
        emptyTitle="No Inventory Records"
        emptyDescription="Create your first catalog SKU and record an initial stock movement."
        emptyActionLabel={canManage ? 'Create First SKU' : undefined}
        onEmptyAction={canManage ? () => setIsProductModalOpen(true) : undefined}
        onRowClick={(item) => {
          setSelectedItem(item);
          setIsDetailDrawerOpen(true);
          fetchMovements(item.product_id);
        }}
      />

      {/* Movement Ledger Detail Drawer */}
      <DetailDrawer
        isOpen={isDetailDrawerOpen && !!selectedItem}
        onClose={() => {
          setIsDetailDrawerOpen(false);
          setSelectedItem(null);
        }}
        title={`Stock Ledger — ${selectedItem?.sku || ''}`}
      >
        {selectedItem && (
          <div className="space-y-6">
            <div>
              <span className="text-[10px] font-mono uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded">
                SKU: {selectedItem.sku}
              </span>
              <h3 className="text-lg font-bold text-white mt-1">{selectedItem.name}</h3>
              <div className="mt-2 p-3 rounded-xl bg-slate-900 border border-slate-800 flex justify-between items-center text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px]">Authoritative Quantity</span>
                  <span className="text-lg font-mono font-bold text-white">
                    {selectedItem.current_quantity} {selectedItem.unit}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Stock Value</span>
                  <span className="text-sm font-mono font-semibold text-emerald-400">
                    ₹{parseFloat(selectedItem.stock_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            </div>

            {/* Movement Ledger Log */}
            <div>
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-slate-400" />
                <span>Immutable Movement History</span>
              </h4>

              {movements.length === 0 ? (
                <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-center text-xs text-slate-500">
                  No stock movements recorded yet for this product.
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                  {movements.map((mov) => (
                    <div
                      key={mov.id}
                      className="p-3 rounded-xl bg-slate-900 border border-slate-800/80 text-xs space-y-1"
                    >
                      <div className="flex justify-between items-center">
                        <span
                          className={`font-mono font-bold text-xs ${
                            mov.direction === 'IN' ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {mov.direction === 'IN' ? '+' : '-'} {mov.quantity} {selectedItem.unit}
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] uppercase font-mono text-slate-300">
                          {mov.movement_type}
                        </span>
                      </div>
                      <div className="flex justify-between text-[11px] text-slate-400">
                        <span>Facility: {mov.location_name || 'Warehouse'}</span>
                        <span className="font-mono">{new Date(mov.created_at).toLocaleString()}</span>
                      </div>
                      {mov.reason && <p className="text-[11px] text-slate-400 italic">"{mov.reason}"</p>}
                      {mov.actor_name && (
                        <span className="text-[10px] text-slate-500 block">Recorded by {mov.actor_name}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </DetailDrawer>

      {/* Create Product Modal */}
      {isProductModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Package className="w-4 h-4 text-emerald-400" />
                <span>Create Catalog Product (SKU)</span>
              </h3>
              <button onClick={() => setIsProductModalOpen(false)} className="text-slate-400 hover:text-slate-200 text-xs">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateProduct} className="p-4 space-y-4 text-xs">
              {formError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 font-semibold">
                  {formError}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">SKU Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. SKU-PROD-001"
                    value={prodSku}
                    onChange={(e) => setProdSku(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 uppercase font-mono placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Unit of Measure</label>
                  <select
                    value={prodUnit}
                    onChange={(e) => setProdUnit(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="UNIT">Units (Count)</option>
                    <option value="PCS">Pieces (PCS)</option>
                    <option value="KG">Kilograms (KG)</option>
                    <option value="GRAM">Grams (G)</option>
                    <option value="LITER">Liters (L)</option>
                    <option value="ML">Milliliters (ML)</option>
                    <option value="BOX">Boxes (BOX)</option>
                    <option value="PACK">Packs (PACK)</option>
                    <option value="METER">Meters (M)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Product Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Industrial Aluminum Bracket"
                  value={prodName}
                  onChange={(e) => setProdName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Category</label>
                <input
                  type="text"
                  placeholder="e.g. Raw Materials / Electronics"
                  value={prodCategory}
                  onChange={(e) => setProdCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Reorder Level</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={prodReorder}
                    onChange={(e) => setProdReorder(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Safety Stock</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={prodSafety}
                    onChange={(e) => setProdSafety(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Cost Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={prodCost}
                    onChange={(e) => setProdCost(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Selling Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={prodSelling}
                    onChange={(e) => setProdSelling(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Preferred Supplier</label>
                <select
                  value={prodSupplierId}
                  onChange={(e) => setProdSupplierId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                >
                  <option value="">None</option>
                  {partners.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsProductModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-slate-200 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create SKU'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Location Modal */}
      {isLocationModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Building2 className="w-4 h-4 text-emerald-400" />
                <span>Register Physical Location</span>
              </h3>
              <button onClick={() => setIsLocationModalOpen(false)} className="text-slate-400 hover:text-slate-200 text-xs">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateLocation} className="p-4 space-y-4 text-xs">
              {formError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 font-semibold">
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Facility Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Central Warehouse / Sector 5 Store"
                  value={locName}
                  onChange={(e) => setLocName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Facility Type</label>
                <select
                  value={locType}
                  onChange={(e) => setLocType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                >
                  <option value="WAREHOUSE">Warehouse</option>
                  <option value="STORE">Retail Store</option>
                  <option value="BRANCH">Branch Facility</option>
                  <option value="OFFICE">Office</option>
                  <option value="STORAGE_UNIT">Storage Unit</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Address</label>
                <textarea
                  rows={2}
                  placeholder="Physical street address..."
                  value={locAddress}
                  onChange={(e) => setLocAddress(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsLocationModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-slate-200 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold disabled:opacity-50"
                >
                  {isSubmitting ? 'Registering...' : 'Register Location'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Record Stock Movement Modal */}
      {isMovementModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-emerald-400" />
                <span>Record Stock Movement</span>
              </h3>
              <button onClick={() => setIsMovementModalOpen(false)} className="text-slate-400 hover:text-slate-200 text-xs">
                ✕
              </button>
            </div>

            <form onSubmit={handleRecordMovement} className="p-4 space-y-4 text-xs">
              {formError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 font-semibold">
                  {formError}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Product (SKU) *</label>
                  <select
                    required
                    value={movProductId}
                    onChange={(e) => setMovProductId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    {inventoryData.items.map((p: any) => (
                      <option key={p.product_id} value={p.product_id}>
                        {p.sku} - {p.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Facility *</label>
                  <select
                    required
                    value={movLocationId}
                    onChange={(e) => setMovLocationId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">Select Location</option>
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Movement Type</label>
                  <select
                    value={movType}
                    onChange={(e) => {
                      const val = e.target.value;
                      setMovType(val);
                      if (val === 'INITIAL_STOCK' || val === 'PURCHASE_RECEIVED' || val === 'RETURN') {
                        setMovDirection('IN');
                      } else if (val === 'SALE' || val === 'DAMAGED') {
                        setMovDirection('OUT');
                      }
                    }}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="INITIAL_STOCK">Initial Stock (IN)</option>
                    <option value="PURCHASE_RECEIVED">Purchase Received (IN)</option>
                    <option value="SALE">Sale Dispatch (OUT)</option>
                    <option value="DAMAGED">Damaged / Spoilage (OUT)</option>
                    <option value="RETURN">Customer Return (IN)</option>
                    <option value="MANUAL_ADJUSTMENT">Manual Adjustment</option>
                  </select>
                </div>

                {movType === 'MANUAL_ADJUSTMENT' && (
                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">Direction</label>
                    <select
                      value={movDirection}
                      onChange={(e) => setMovDirection(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                    >
                      <option value="IN">IN (Add Stock)</option>
                      <option value="OUT">OUT (Reduce Stock)</option>
                    </select>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Quantity *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={movQuantity}
                    onChange={(e) => setMovQuantity(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Unit Cost (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="Optional"
                    value={movUnitCost}
                    onChange={(e) => setMovUnitCost(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Reason / Notes</label>
                <textarea
                  rows={2}
                  placeholder="Audit reason for stock movement..."
                  value={movReason}
                  onChange={(e) => setMovReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsMovementModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-slate-200 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold disabled:opacity-50"
                >
                  {isSubmitting ? 'Recording...' : 'Commit to Ledger'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inter-Location Transfer Modal */}
      {isTransferModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ArrowLeftRight className="w-4 h-4 text-indigo-400" />
                <span>Inter-Location Stock Transfer</span>
              </h3>
              <button onClick={() => setIsTransferModalOpen(false)} className="text-slate-400 hover:text-slate-200 text-xs">
                ✕
              </button>
            </div>

            <form onSubmit={handleTransfer} className="p-4 space-y-4 text-xs">
              {formError && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 font-semibold">
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Product (SKU) *</label>
                <select
                  required
                  value={trfProductId}
                  onChange={(e) => setTrfProductId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                >
                  {inventoryData.items.map((p: any) => (
                    <option key={p.product_id} value={p.product_id}>
                      {p.sku} - {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Source Facility *</label>
                  <select
                    required
                    value={trfSourceLocId}
                    onChange={(e) => setTrfSourceLocId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">Select Source</option>
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Destination Facility *</label>
                  <select
                    required
                    value={trfDestLocId}
                    onChange={(e) => setTrfDestLocId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="">Select Destination</option>
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Transfer Quantity *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={trfQuantity}
                  onChange={(e) => setTrfQuantity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 font-mono focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Reason / Notes</label>
                <textarea
                  rows={2}
                  placeholder="Reason for inter-location movement..."
                  value={trfReason}
                  onChange={(e) => setTrfReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsTransferModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-slate-200 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold disabled:opacity-50"
                >
                  {isSubmitting ? 'Transferring...' : 'Execute Atomic Transfer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
