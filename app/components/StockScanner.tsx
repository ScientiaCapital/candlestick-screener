'use client';

import React, { useState, useEffect } from 'react';
import { PatternSelector } from './PatternSelector';
import { StockScannerProps, ScanRequest, Pattern } from '@/app/lib/types';
import { 
  MagnifyingGlassIcon, 
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';

interface FormErrors {
  minPrice?: string;
  maxPrice?: string;
  volume?: string;
  priceRange?: string;
}

interface FormData {
  selectedPattern: string;
  timeframe: string;
  minVolume: number | null;
  minPrice: number | null;
  maxPrice: number | null;
  patternType: 'all' | 'bullish' | 'bearish' | 'neutral';
}

export function StockScanner({ onScan, loading = false, error = null }: StockScannerProps) {
  const [formData, setFormData] = useState<FormData>({
    selectedPattern: '',
    timeframe: '1d',
    minVolume: null,
    minPrice: null,
    maxPrice: null,
    patternType: 'all',
  });

  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [hasScanned, setHasScanned] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Mock patterns for now - will be replaced with actual data
  const mockPatterns: Pattern[] = [
    { name: 'hammer', displayName: 'Hammer', type: 'bullish' },
    { name: 'doji', displayName: 'Doji', type: 'neutral' },
    { name: 'shooting_star', displayName: 'Shooting Star', type: 'bearish' },
  ];

  // Check if viewport is mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Enter' && formData.selectedPattern && !loading) {
        event.preventDefault();
        handleScan();
      }
      
      if (event.ctrlKey && event.key === 'r') {
        event.preventDefault();
        handleReset();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [formData.selectedPattern, loading]);

  const validateForm = (): FormErrors => {
    const errors: FormErrors = {};

    if (formData.minVolume !== null && formData.minVolume < 0) {
      errors.volume = 'Volume must be a positive number';
    }

    if (formData.minPrice !== null && formData.minPrice < 0) {
      errors.minPrice = 'Minimum price must be positive';
    }

    if (formData.maxPrice !== null && formData.maxPrice < 0) {
      errors.maxPrice = 'Maximum price must be positive';
    }

    if (
      formData.minPrice !== null && 
      formData.maxPrice !== null && 
      formData.minPrice >= formData.maxPrice
    ) {
      errors.priceRange = 'Minimum price must be less than maximum price';
    }

    return errors;
  };

  const handleScan = () => {
    if (!formData.selectedPattern || loading) return;

    const errors = validateForm();
    setFormErrors(errors);

    if (Object.keys(errors).length > 0) return;

    const scanRequest: ScanRequest = {
      pattern: formData.selectedPattern,
      timeframe: formData.timeframe,
      minVolume: formData.minVolume,
      minPrice: formData.minPrice,
      maxPrice: formData.maxPrice,
    };

    onScan(scanRequest);
    setHasScanned(true);
  };

  const handleReset = () => {
    setFormData({
      selectedPattern: '',
      timeframe: '1d',
      minVolume: null,
      minPrice: null,
      maxPrice: null,
      patternType: 'all',
    });
    setFormErrors({});
    setHasScanned(false);
    setShowAdvancedFilters(false);
  };

  const handlePatternSelect = (pattern: string) => {
    setFormData(prev => ({ ...prev, selectedPattern: pattern }));
    setFormErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors.priceRange;
      return newErrors;
    });
  };

  const handleInputChange = (field: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear related errors when user starts typing
    if (field === 'minVolume') {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.volume;
        return newErrors;
      });
    }
    if (field === 'minPrice' || field === 'maxPrice') {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.minPrice;
        delete newErrors.maxPrice;
        delete newErrors.priceRange;
        return newErrors;
      });
    }
  };

  const handleNumberInput = (field: keyof FormData, value: string) => {
    const numValue = value === '' ? null : parseFloat(value);
    handleInputChange(field, numValue);
  };

  const isFormValid = Boolean(formData.selectedPattern) && Object.keys(formErrors).length === 0;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <MagnifyingGlassIcon className="h-6 w-6 mr-2 text-blue-600" />
          Stock Scanner
        </h2>
        
        {hasScanned && (
          <button
            type="button"
            onClick={handleReset}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            disabled={loading}
          >
            <ArrowPathIcon className="h-4 w-4 mr-1" />
            Reset
          </button>
        )}
      </div>

      <form 
        role="form"
        onSubmit={(e) => {
          e.preventDefault();
          handleScan();
        }}
        className="space-y-6"
      >
        {/* Pattern Selection */}
        <div>
          <PatternSelector
            patterns={mockPatterns}
            selectedPattern={formData.selectedPattern}
            onPatternSelect={handlePatternSelect}
            loading={false}
            error={null}
          />
        </div>

        {/* Timeframe Selection */}
        <div>
          <label htmlFor="timeframe" className="block text-sm font-medium text-gray-700 mb-2">
            Timeframe
          </label>
          <select
            id="timeframe"
            value={formData.timeframe}
            onChange={(e) => handleInputChange('timeframe', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            disabled={loading}
          >
            <option value="1m">1 Minute</option>
            <option value="5m">5 Minutes</option>
            <option value="15m">15 Minutes</option>
            <option value="1h">1 Hour</option>
            <option value="1d">1 Day</option>
            <option value="1w">1 Week</option>
          </select>
        </div>

        {/* Mobile Filter Toggle */}
        {isMobile && (
          <button
            type="button"
            onClick={() => setShowMobileFilters(!showMobileFilters)}
            className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 rounded-md text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <span className="flex items-center">
              {showMobileFilters ? <EyeSlashIcon className="h-4 w-4 mr-2" /> : <EyeIcon className="h-4 w-4 mr-2" />}
              {showMobileFilters ? 'Hide' : 'Show'} Filters
            </span>
            {showMobileFilters ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
          </button>
        )}

        {/* Basic Filters */}
        <div className={`space-y-4 ${isMobile && !showMobileFilters ? 'hidden' : ''}`}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Minimum Volume */}
            <div>
              <label htmlFor="minVolume" className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Volume
              </label>
              <input
                id="minVolume"
                type="number"
                min="0"
                step="1000"
                value={formData.minVolume?.toString() || ''}
                onChange={(e) => handleNumberInput('minVolume', e.target.value)}
                onBlur={() => setFormErrors(validateForm())}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                placeholder="e.g., 1000000"
                disabled={loading}
              />
              {formErrors.volume && (
                <p className="mt-1 text-sm text-red-600">{formErrors.volume}</p>
              )}
            </div>

            {/* Minimum Price */}
            <div>
              <label htmlFor="minPrice" className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Price ($)
              </label>
              <input
                id="minPrice"
                type="number"
                min="0"
                step="0.01"
                value={formData.minPrice?.toString() || ''}
                onChange={(e) => handleNumberInput('minPrice', e.target.value)}
                onBlur={() => setFormErrors(validateForm())}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                placeholder="e.g., 5.00"
                disabled={loading}
              />
              {formErrors.minPrice && (
                <p className="mt-1 text-sm text-red-600">{formErrors.minPrice}</p>
              )}
            </div>

            {/* Maximum Price */}
            <div>
              <label htmlFor="maxPrice" className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Price ($)
              </label>
              <input
                id="maxPrice"
                type="number"
                min="0"
                step="0.01"
                value={formData.maxPrice?.toString() || ''}
                onChange={(e) => handleNumberInput('maxPrice', e.target.value)}
                onBlur={() => setFormErrors(validateForm())}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                placeholder="e.g., 100.00"
                disabled={loading}
              />
              {formErrors.maxPrice && (
                <p className="mt-1 text-sm text-red-600">{formErrors.maxPrice}</p>
              )}
            </div>
          </div>

          {/* Price Range Error */}
          {formErrors.priceRange && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{formErrors.priceRange}</p>
            </div>
          )}
        </div>

        {/* Advanced Filters Toggle */}
        <button
          type="button"
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          className="flex items-center text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          disabled={loading}
        >
          <AdjustmentsHorizontalIcon className="h-4 w-4 mr-2" />
          Advanced Filters
          {showAdvancedFilters ? (
            <ChevronUpIcon className="h-4 w-4 ml-1" />
          ) : (
            <ChevronDownIcon className="h-4 w-4 ml-1" />
          )}
        </button>

        {/* Advanced Filters */}
        {showAdvancedFilters && (
          <div className="bg-gray-50 rounded-md p-4 space-y-4">
            <div>
              <label htmlFor="patternType" className="block text-sm font-medium text-gray-700 mb-2">
                Pattern Type Filter
              </label>
              <select
                id="patternType"
                value={formData.patternType}
                onChange={(e) => handleInputChange('patternType', e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                disabled={loading}
              >
                <option value="all">All Patterns</option>
                <option value="bullish">Bullish Only</option>
                <option value="bearish">Bearish Only</option>
                <option value="neutral">Neutral Only</option>
              </select>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div role="alert" className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-3" />
              <div>
                <h3 className="text-sm font-medium text-red-800">Scan Error</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Scan Button */}
        <div className="flex justify-center">
          <button
            type="submit"
            disabled={!isFormValid || loading}
            className={`
              px-8 py-3 rounded-md font-medium text-white transition-all duration-200
              ${isFormValid && !loading
                ? 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 shadow-lg hover:shadow-xl'
                : 'bg-gray-400 cursor-not-allowed'
              }
            `}
            aria-label={loading ? 'Scanning in progress' : 'Scan stocks'}
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2"></div>
                Scanning...
              </div>
            ) : (
              <div className="flex items-center">
                <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
                Scan Stocks
              </div>
            )}
          </button>
        </div>

        {/* Loading State Message */}
        {loading && (
          <div className="text-center">
            <p className="text-sm text-gray-600">Scanning for patterns across the market...</p>
          </div>
        )}
      </form>
    </div>
  );
}