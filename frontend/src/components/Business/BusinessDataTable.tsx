import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import { BusinessLoadingState } from './BusinessLoadingState';
import { BusinessEmptyState } from './BusinessEmptyState';

export interface ColumnDef<T> {
  key: string;
  header: string;
  render?: (row: T, index: number) => React.ReactNode;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  className?: string;
  headerClassName?: string;
}

export interface BusinessDataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  keyExtractor: (row: T, index: number) => string;
  loading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
  onRowClick?: (row: T, index: number) => void;
  className?: string;
  tableClassName?: string;
  defaultSortKey?: string;
  defaultSortDir?: 'asc' | 'desc';
}

export function BusinessDataTable<T extends Record<string, any>>({
  columns,
  data,
  keyExtractor,
  loading = false,
  emptyTitle = 'No Records Found',
  emptyDescription = 'There are no business records matching the current criteria.',
  emptyActionLabel,
  onEmptyAction,
  onRowClick,
  className = '',
  tableClassName = '',
  defaultSortKey,
  defaultSortDir = 'desc',
}: BusinessDataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | undefined>(defaultSortKey);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(defaultSortDir);

  const handleHeaderClick = (col: ColumnDef<T>) => {
    if (!col.sortable) return;

    if (sortKey === col.key) {
      setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(col.key);
      setSortDir('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!sortKey || !data || data.length === 0) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();

      return sortDir === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
    });
  }, [data, sortKey, sortDir]);

  if (loading) {
    return <BusinessLoadingState type="table" rows={6} className={className} />;
  }

  if (!data || data.length === 0) {
    return (
      <BusinessEmptyState
        title={emptyTitle}
        description={emptyDescription}
        actionLabel={emptyActionLabel}
        onAction={onEmptyAction}
        className={className}
      />
    );
  }

  return (
    <div
      role="region"
      aria-label={emptyTitle || 'Data Table'}
      tabIndex={0}
      className={`rounded-2xl bg-[#0B0F19]/90 border border-slate-800/80 shadow-xl overflow-hidden focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-emerald-500/30 ${className}`}
    >
      <div className="overflow-x-auto no-scrollbar">
        <table className={`w-full text-left text-xs text-slate-300 border-collapse ${tableClassName}`}>
          {/* Table Header */}
          <thead className="bg-slate-900/60 border-b border-slate-800/80 uppercase text-[10px] tracking-wider text-slate-400 font-semibold select-none">
            <tr>
              {columns.map(col => {
                const isSorted = sortKey === col.key;
                const alignClass =
                  col.align === 'right'
                    ? 'text-right'
                    : col.align === 'center'
                    ? 'text-center'
                    : 'text-left';

                return (
                  <th
                    key={col.key}
                    scope="col"
                    role={col.sortable ? 'columnheader' : undefined}
                    aria-sort={
                      col.sortable
                        ? isSorted
                          ? sortDir === 'asc'
                            ? 'ascending'
                            : 'descending'
                          : 'none'
                        : undefined
                    }
                    tabIndex={col.sortable ? 0 : undefined}
                    onClick={() => handleHeaderClick(col)}
                    onKeyDown={e => {
                      if (col.sortable && (e.key === 'Enter' || e.key === ' ')) {
                        e.preventDefault();
                        handleHeaderClick(col);
                      }
                    }}
                    className={`px-4 sm:px-6 py-3.5 transition-colors focus-visible:outline-none focus-visible:bg-slate-800/50 focus-visible:text-slate-100 ${
                      col.sortable
                        ? 'cursor-pointer hover:text-slate-200 hover:bg-slate-800/30'
                        : ''
                    } ${alignClass} ${col.headerClassName || ''}`}
                  >
                    <div
                      className={`inline-flex items-center gap-1.5 ${
                        col.align === 'right' ? 'justify-end w-full' : ''
                      }`}
                    >
                      <span>{col.header}</span>
                      {col.sortable && (
                        <span className="text-slate-500" aria-hidden="true">
                          {isSorted ? (
                            sortDir === 'asc' ? (
                              <ChevronUp className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <ChevronDown className="w-3 h-3 text-emerald-400" />
                            )
                          ) : (
                            <ChevronsUpDown className="w-3 h-3 opacity-40 hover:opacity-100" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="divide-y divide-slate-800/40 font-sans">
            {sortedData.map((row, rowIdx) => {
              const rowKey = keyExtractor(row, rowIdx);

              return (
                <tr
                  key={rowKey}
                  tabIndex={onRowClick ? 0 : undefined}
                  role={onRowClick ? 'button' : undefined}
                  aria-label={onRowClick ? `Row ${rowIdx + 1}` : undefined}
                  onClick={() => onRowClick && onRowClick(row, rowIdx)}
                  onKeyDown={e => {
                    if (onRowClick && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault();
                      onRowClick(row, rowIdx);
                    }
                  }}
                  className={`group transition-colors duration-150 focus-visible:outline-none focus-visible:bg-slate-800/60 focus-visible:ring-1 focus-visible:ring-emerald-500/50 ${
                    onRowClick
                      ? 'cursor-pointer hover:bg-slate-800/40 hover:text-white'
                      : 'hover:bg-slate-800/20'
                  }`}
                >
                  {columns.map(col => {
                    const alignClass =
                      col.align === 'right'
                        ? 'text-right'
                        : col.align === 'center'
                        ? 'text-center'
                        : 'text-left';

                    const cellContent = col.render
                      ? col.render(row, rowIdx)
                      : row[col.key] !== undefined && row[col.key] !== null
                      ? String(row[col.key])
                      : '—';

                    return (
                      <td
                        key={col.key}
                        className={`px-4 sm:px-6 py-3.5 whitespace-nowrap ${alignClass} ${
                          col.className || ''
                        }`}
                      >
                        {cellContent}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
