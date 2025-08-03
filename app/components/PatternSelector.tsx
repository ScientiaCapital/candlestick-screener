'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChevronDownIcon, XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { PatternSelectorProps, Pattern } from '@/app/lib/types';

interface ExtendedPatternSelectorProps extends PatternSelectorProps {
  groupByType?: boolean;
  showDescriptions?: boolean;
}

export function PatternSelector({
  patterns,
  selectedPattern,
  onPatternSelect,
  loading = false,
  error = null,
  groupByType = false,
  showDescriptions = false,
}: ExtendedPatternSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter patterns based on search term
  const filteredPatterns = patterns.filter(pattern =>
    pattern.displayName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pattern.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group patterns by type if requested
  const groupedPatterns = groupByType
    ? {
        bullish: filteredPatterns.filter(p => p.type === 'bullish'),
        bearish: filteredPatterns.filter(p => p.type === 'bearish'),
        neutral: filteredPatterns.filter(p => p.type === 'neutral'),
      }
    : null;

  // Get selected pattern display name
  const selectedPatternDisplay = patterns.find(p => p.name === selectedPattern)?.displayName || '';

  // Handle clicking outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
        setFocusedIndex(-1);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (!isOpen) {
      if (event.key === 'Enter' || event.key === ' ' || event.key === 'ArrowDown') {
        event.preventDefault();
        setIsOpen(true);
        setFocusedIndex(0);
      }
      return;
    }

    switch (event.key) {
      case 'Escape':
        event.preventDefault();
        setIsOpen(false);
        setSearchTerm('');
        setFocusedIndex(-1);
        inputRef.current?.focus();
        break;
      case 'ArrowDown':
        event.preventDefault();
        setFocusedIndex(prev => Math.min(prev + 1, filteredPatterns.length - 1));
        break;
      case 'ArrowUp':
        event.preventDefault();
        setFocusedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        event.preventDefault();
        if (focusedIndex >= 0 && filteredPatterns[focusedIndex]) {
          handlePatternSelect(filteredPatterns[focusedIndex].name);
        }
        break;
    }
  };

  const handlePatternSelect = (patternName: string) => {
    onPatternSelect(patternName);
    setIsOpen(false);
    setSearchTerm('');
    setFocusedIndex(-1);
  };

  const handleClearSelection = () => {
    onPatternSelect('');
  };

  const getPatternTypeColor = (type: Pattern['type']) => {
    switch (type) {
      case 'bullish':
        return 'text-green-600 bg-green-50';
      case 'bearish':
        return 'text-red-600 bg-red-50';
      case 'neutral':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const renderPattern = (pattern: Pattern, index: number) => (
    <li
      key={pattern.name}
      className={`px-3 py-2 cursor-pointer transition-colors ${
        index === focusedIndex
          ? 'bg-blue-100 text-blue-900'
          : 'hover:bg-gray-100'
      }`}
      onClick={() => handlePatternSelect(pattern.name)}
      role="option"
      aria-selected={pattern.name === selectedPattern}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPatternTypeColor(pattern.type)}`}>
            {pattern.type}
          </span>
          <span className="font-medium">{pattern.displayName}</span>
        </div>
      </div>
      {showDescriptions && pattern.description && (
        <p className="text-sm text-gray-500 mt-1 ml-2">{pattern.description}</p>
      )}
    </li>
  );

  const renderGroupedPatterns = () => {
    if (!groupedPatterns) return null;

    return (
      <>
        {groupedPatterns.bullish.length > 0 && (
          <div>
            <div className="px-3 py-2 text-sm font-semibold text-gray-900 bg-gray-50">
              Bullish Patterns
            </div>
            {groupedPatterns.bullish.map((pattern, index) => renderPattern(pattern, index))}
          </div>
        )}
        {groupedPatterns.bearish.length > 0 && (
          <div>
            <div className="px-3 py-2 text-sm font-semibold text-gray-900 bg-gray-50">
              Bearish Patterns
            </div>
            {groupedPatterns.bearish.map((pattern, index) => 
              renderPattern(pattern, index + groupedPatterns.bullish.length)
            )}
          </div>
        )}
        {groupedPatterns.neutral.length > 0 && (
          <div>
            <div className="px-3 py-2 text-sm font-semibold text-gray-900 bg-gray-50">
              Neutral Patterns
            </div>
            {groupedPatterns.neutral.map((pattern, index) => 
              renderPattern(pattern, index + groupedPatterns.bullish.length + groupedPatterns.bearish.length)
            )}
          </div>
        )}
      </>
    );
  };

  if (loading) {
    return (
      <div className="w-full">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Candlestick Pattern
        </label>
        <div className="relative">
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 cursor-not-allowed"
            placeholder="Loading patterns..."
            disabled
            aria-label="Select pattern"
          />
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Candlestick Pattern
        </label>
        <div className="relative">
          <input
            type="text"
            className="w-full px-3 py-2 border border-red-300 rounded-md bg-red-50 cursor-not-allowed"
            placeholder="Error loading patterns"
            disabled
            aria-label="Select pattern"
          />
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            <XMarkIcon className="h-4 w-4 text-red-500" />
          </div>
        </div>
        <p className="mt-1 text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (patterns.length === 0) {
    return (
      <div className="w-full">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Candlestick Pattern
        </label>
        <div className="relative">
          <input
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 cursor-not-allowed"
            placeholder="No patterns available"
            disabled
            aria-label="Select pattern"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full" ref={dropdownRef}>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Candlestick Pattern
      </label>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder={selectedPattern ? selectedPatternDisplay : "Select a candlestick pattern"}
          value={isOpen ? searchTerm : selectedPatternDisplay}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-label="Select pattern"
          role="combobox"
        />
        <div className="absolute inset-y-0 right-0 flex items-center">
          {selectedPattern && (
            <button
              type="button"
              className="p-1 mr-1 text-gray-400 hover:text-gray-600"
              onClick={handleClearSelection}
              aria-label="Clear selection"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          )}
          <button
            type="button"
            className="p-2 text-gray-400 hover:text-gray-600"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="Toggle dropdown"
          >
            <ChevronDownIcon className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {isOpen && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
            {filteredPatterns.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500">
                No patterns found
              </div>
            ) : (
              <ul role="listbox" aria-label="Pattern options">
                {groupByType ? renderGroupedPatterns() : filteredPatterns.map(renderPattern)}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}