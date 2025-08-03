'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { 
  ChevronUpIcon, 
  ChevronDownIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { ResultsTableProps, ScanResult, SortConfig } from '@/app/lib/types';

interface ExtendedResultsTableProps extends ResultsTableProps {
  emptyMessage?: string;
  onRetry?: () => void;
  onRowClick?: (result: ScanResult) => void;
  sortConfig?: SortConfig;
  virtualScrolling?: boolean;
}

export function ResultsTable({
  results,
  loading = false,
  error = null,
  emptyMessage = "No results found. Try adjusting your search criteria.",
  onSort,
  onRetry,
  onRowClick,
  sortConfig,
  virtualScrolling = false,
}: ExtendedResultsTableProps) {
  const [currentSortConfig, setCurrentSortConfig] = useState<SortConfig | null>(sortConfig || null);
  const [isMobile, setIsMobile] = useState(false);

  // Check viewport size for responsive behavior
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Format currency values
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Format large numbers (volume)
  const formatVolume = (volume: number): string => {
    if (volume === 0) return '0';
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(1)}B`;
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(1)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(1)}K`;
    return volume.toString();
  };

  // Format price change
  const formatChange = (change: number, changePercent: number): { text: string; className: string } => {
    // For positive changes, we need to add '+' since formatCurrency doesn't include it
    // For negative changes, formatCurrency already includes the '-'
    // For zero, we want to show '+$0.00'
    let formattedAmount: string;
    if (change > 0) {
      formattedAmount = `+${formatCurrency(change)}`;
    } else if (change < 0) {
      formattedAmount = formatCurrency(change); // Already has negative sign
    } else {
      formattedAmount = `+${formatCurrency(change)}`; // +$0.00
    }
    
    const changeText = `${formattedAmount} (${change >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)`;
    const className = change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600';
    
    return { text: changeText, className };
  };

  // Handle column sorting
  const handleSort = (column: keyof ScanResult) => {
    if (!onSort) return;

    const direction = 
      currentSortConfig?.column === column && currentSortConfig?.direction === 'asc' 
        ? 'desc' 
        : 'asc';

    const newSortConfig = { column, direction };
    setCurrentSortConfig(newSortConfig);
    onSort(column, direction);
  };

  // Handle row click
  const handleRowClick = (result: ScanResult) => {
    if (onRowClick) {
      onRowClick(result);
    }
  };

  // Handle keyboard navigation for rows
  const handleRowKeyDown = (event: React.KeyboardEvent, result: ScanResult) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleRowClick(result);
    }
  };

  // Get sort icon for column
  const getSortIcon = (column: keyof ScanResult) => {
    if (currentSortConfig?.column !== column) return null;
    
    return currentSortConfig.direction === 'asc' ? (
      <ChevronUpIcon className="h-4 w-4" />
    ) : (
      <ChevronDownIcon className="h-4 w-4" />
    );
  };

  // Get ARIA sort attribute for column
  const getAriaSortAttribute = (column: keyof ScanResult) => {
    if (currentSortConfig?.column !== column) return 'none';
    return currentSortConfig.direction === 'asc' ? 'ascending' : 'descending';
  };

  // Render skeleton rows for loading state
  const renderSkeletonRows = () => {
    return Array.from({ length: 5 }).map((_, index) => (
      <tr key={`skeleton-${index}`} className="animate-pulse">
        <td className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded w-16"></div>
        </td>
        <td className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded w-32"></div>
        </td>
        <td className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded w-20"></div>
        </td>
        <td className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded w-16"></div>
          <div className="h-2 bg-gray-200 rounded w-full mt-1"></div>
        </td>
        <td className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded w-20"></div>
        </td>
        <td className="px-6 py-4">
          <div className="h-4 bg-gray-200 rounded w-24"></div>
        </td>
        {!isMobile && (
          <td className="px-6 py-4">
            <div className="h-4 bg-gray-200 rounded w-16"></div>
          </td>
        )}
      </tr>
    ));
  };

  // Render signal strength progress bar
  const renderSignalBar = (signal: number) => (
    <div className="flex items-center space-x-2">
      <span className="text-sm font-medium w-8">{signal}</span>
      <div className="flex-1 bg-gray-200 rounded-full h-2" role="progressbar" aria-valuenow={signal} aria-valuemin={0} aria-valuemax={100}>
        <div 
          className={`h-2 rounded-full transition-all duration-300 ${
            signal >= 80 ? 'bg-green-500' : 
            signal >= 60 ? 'bg-yellow-500' : 
            'bg-red-500'
          }`}
          style={{ width: `${signal}%` }}
        ></div>
      </div>
    </div>
  );

  // Render pattern badge
  const renderPattern = (pattern: string) => (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
      {pattern.replace('_', ' ')}
    </span>
  );

  // Render table header
  const renderHeader = () => (
    <thead className="bg-gray-50">
      <tr>
        <th className="px-6 py-3 text-left">
          {onSort ? (
            <button
              onClick={() => handleSort('symbol')}
              className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700 focus:outline-none focus:text-gray-700"
              aria-sort={getAriaSortAttribute('symbol')}
              disabled={loading}
              aria-label="Sort by symbol"
            >
              <span>Symbol</span>
              {getSortIcon('symbol')}
            </button>
          ) : (
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</span>
          )}
        </th>
        {!isMobile && (
          <th className="px-6 py-3 text-left">
            {onSort ? (
              <button
                onClick={() => handleSort('companyName')}
                className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700 focus:outline-none focus:text-gray-700"
                aria-sort={getAriaSortAttribute('companyName')}
                disabled={loading}
                aria-label="Sort by company"
              >
                <span>Company</span>
                {getSortIcon('companyName')}
              </button>
            ) : (
              <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Company</span>
            )}
          </th>
        )}
        <th className="px-6 py-3 text-left">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Pattern</span>
        </th>
        <th className="px-6 py-3 text-left">
          {onSort ? (
            <button
              onClick={() => handleSort('signal')}
              className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700 focus:outline-none focus:text-gray-700"
              aria-sort={getAriaSortAttribute('signal')}
              disabled={loading}
              aria-label="Sort by signal"
            >
              <span>Signal</span>
              {getSortIcon('signal')}
            </button>
          ) : (
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Signal</span>
          )}
        </th>
        <th className="px-6 py-3 text-left">
          {onSort ? (
            <button
              onClick={() => handleSort('price')}
              className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700 focus:outline-none focus:text-gray-700"
              aria-sort={getAriaSortAttribute('price')}
              disabled={loading}
              aria-label="Sort by price"
            >
              <span>Price</span>
              {getSortIcon('price')}
            </button>
          ) : (
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Price</span>
          )}
        </th>
        <th className="px-6 py-3 text-left">
          {onSort ? (
            <button
              onClick={() => handleSort('change')}
              className="flex items-center space-x-1 text-xs font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700 focus:outline-none focus:text-gray-700"
              aria-sort={getAriaSortAttribute('change')}
              disabled={loading}
              aria-label="Sort by change"
            >
              <span>Change</span>
              {getSortIcon('change')}
            </button>
          ) : (
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Change</span>
          )}
        </th>
        {!isMobile && (
          <th className="px-6 py-3 text-left">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Volume</span>
          </th>
        )}
      </tr>
    </thead>
  );

  // Render data rows
  const renderDataRows = () => {
    if (virtualScrolling && results.length > 100) {
      // For very large datasets, only render first 50 items (simplified virtual scrolling)
      return results.slice(0, 50).map((result, index) => renderDataRow(result, index));
    }
    
    return results.map((result, index) => renderDataRow(result, index));
  };

  // Render individual data row
  const renderDataRow = (result: ScanResult, index: number) => {
    const changeInfo = formatChange(result.change, result.changePercent);
    const isClickable = Boolean(onRowClick);
    
    return (
      <tr 
        key={`${result.symbol}-${index}`}
        className={`
          bg-white border-b hover:bg-gray-50 transition-colors
          ${isClickable ? 'cursor-pointer' : ''}
        `}
        onClick={isClickable ? () => handleRowClick(result) : undefined}
        onKeyDown={isClickable ? (e) => handleRowKeyDown(e, result) : undefined}
        tabIndex={isClickable ? 0 : undefined}
        aria-label={isClickable ? `View details for ${result.symbol}` : undefined}
      >
        <td className="px-6 py-4 text-sm font-medium text-gray-900">
          {result.symbol}
        </td>
        {!isMobile && (
          <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
            {result.companyName}
          </td>
        )}
        <td className="px-6 py-4">
          {renderPattern(result.pattern)}
        </td>
        <td className="px-6 py-4">
          {renderSignalBar(result.signal)}
        </td>
        <td className="px-6 py-4 text-sm font-medium text-gray-900">
          {formatCurrency(result.price)}
        </td>
        <td className={`px-6 py-4 text-sm font-medium ${changeInfo.className}`}>
          {changeInfo.text}
        </td>
        {!isMobile && (
          <td className="px-6 py-4 text-sm text-gray-600">
            {formatVolume(result.volume || 0)}
          </td>
        )}
      </tr>
    );
  };

  // Handle error state
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8" role="alert">
        <div className="flex items-center justify-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-400 mr-4" />
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Results</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Retry
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Handle empty state
  if (!loading && results.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="text-center">
          <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Results Found</h3>
          <p className="text-gray-600">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Loading indicator */}
      {loading && (
        <div className="px-6 py-4 bg-blue-50 border-b" role="status">
          <div className="flex items-center">
            <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full mr-2"></div>
            <span className="text-sm text-blue-700">Loading results...</span>
          </div>
        </div>
      )}

      {/* Table */}
      <div className={`${typeof window !== 'undefined' && window.innerWidth <= 320 ? 'overflow-x-auto' : ''}`}>
        <table className="min-w-full divide-y divide-gray-200" aria-label="Scan results">
          {renderHeader()}
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? renderSkeletonRows() : renderDataRows()}
          </tbody>
        </table>
      </div>

      {/* Results count */}
      {!loading && results.length > 0 && (
        <div className="px-6 py-3 bg-gray-50 border-t">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">
              Showing {results.length} result{results.length !== 1 ? 's' : ''}
            </span>
            <div className="flex items-center text-sm text-gray-500">
              <ChartBarIcon className="h-4 w-4 mr-1" />
              <span>Market scan completed</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}