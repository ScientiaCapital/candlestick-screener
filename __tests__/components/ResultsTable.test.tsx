import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ResultsTable } from '../../app/components/ResultsTable';
import { ScanResult, SortConfig } from '../../app/lib/types';

// Mock ScanResult data
const mockResults: ScanResult[] = [
  {
    symbol: 'AAPL',
    companyName: 'Apple Inc.',
    pattern: 'hammer',
    signal: 85,
    price: 150.25,
    change: 2.45,
    changePercent: 1.66,
    volume: 52000000,
    timestamp: '2024-01-15T14:30:00Z',
  },
  {
    symbol: 'GOOGL',
    companyName: 'Alphabet Inc.',
    pattern: 'doji',
    signal: 72,
    price: 2750.80,
    change: -15.20,
    changePercent: -0.55,
    volume: 1200000,
    timestamp: '2024-01-15T14:30:00Z',
  },
  {
    symbol: 'MSFT',
    companyName: 'Microsoft Corporation',
    pattern: 'shooting_star',
    signal: 91,
    price: 310.50,
    change: 5.75,
    changePercent: 1.89,
    volume: 28000000,
    timestamp: '2024-01-15T14:30:00Z',
  },
  {
    symbol: 'TSLA',
    companyName: 'Tesla, Inc.',
    pattern: 'hammer',
    signal: 68,
    price: 205.15,
    change: -8.35,
    changePercent: -3.91,
    volume: 45000000,
    timestamp: '2024-01-15T14:30:00Z',
  },
];

const defaultProps = {
  results: mockResults,
};

describe('ResultsTable Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the results table with headers', () => {
      render(<ResultsTable {...defaultProps} />);
      
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('Symbol')).toBeInTheDocument();
      expect(screen.getByText('Company')).toBeInTheDocument();
      expect(screen.getByText('Pattern')).toBeInTheDocument();
      expect(screen.getByText('Signal')).toBeInTheDocument();
      expect(screen.getByText('Price')).toBeInTheDocument();
      expect(screen.getByText('Change')).toBeInTheDocument();
      expect(screen.getByText('Volume')).toBeInTheDocument();
    });

    it('should render all result rows', () => {
      render(<ResultsTable {...defaultProps} />);
      
      mockResults.forEach(result => {
        expect(screen.getByText(result.symbol)).toBeInTheDocument();
        expect(screen.getByText(result.companyName)).toBeInTheDocument();
      });
    });

    it('should display stock prices with proper formatting', () => {
      render(<ResultsTable {...defaultProps} />);
      
      expect(screen.getByText('$150.25')).toBeInTheDocument();
      expect(screen.getByText('$2,750.80')).toBeInTheDocument();
      expect(screen.getByText('$310.50')).toBeInTheDocument();
    });

    it('should display price changes with proper formatting and colors', () => {
      render(<ResultsTable {...defaultProps} />);
      
      // Positive changes should be green
      const positiveChange = screen.getByText('+$2.45 (+1.66%)');
      expect(positiveChange).toBeInTheDocument();
      expect(positiveChange).toHaveClass('text-green-600');
      
      // Negative changes should be red
      const negativeChange = screen.getByText('-$15.20 (-0.55%)');
      expect(negativeChange).toBeInTheDocument();
      expect(negativeChange).toHaveClass('text-red-600');
    });

    it('should display volume with proper formatting', () => {
      render(<ResultsTable {...defaultProps} />);
      
      expect(screen.getByText('52.0M')).toBeInTheDocument(); // 52,000,000
      expect(screen.getByText('1.2M')).toBeInTheDocument(); // 1,200,000
    });

    it('should display signal strength with progress bars', () => {
      render(<ResultsTable {...defaultProps} />);
      
      // Check for signal values
      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText('72')).toBeInTheDocument();
      expect(screen.getByText('91')).toBeInTheDocument();
      expect(screen.getByText('68')).toBeInTheDocument();
      
      // Check for progress bars
      const progressBars = screen.getAllByRole('progressbar');
      expect(progressBars).toHaveLength(4);
    });

    it('should display pattern names with appropriate styling', () => {
      render(<ResultsTable {...defaultProps} />);
      
      const patterns = screen.getAllByText(/hammer|doji|shooting_star/);
      expect(patterns.length).toBeGreaterThan(0);
    });
  });

  describe('Empty States', () => {
    it('should show empty state when no results', () => {
      render(<ResultsTable {...defaultProps} results={[]} />);
      
      expect(screen.getByRole('heading', { name: /no results found/i })).toBeInTheDocument();
      expect(screen.getByText(/try adjusting your search criteria/i)).toBeInTheDocument();
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('should show empty state with custom message when provided', () => {
      render(<ResultsTable {...defaultProps} results={[]} emptyMessage="Custom empty message" />);
      
      expect(screen.getByText('Custom empty message')).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('should show loading state when loading prop is true', () => {
      render(<ResultsTable {...defaultProps} loading={true} />);
      
      expect(screen.getByText(/loading results/i)).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument(); // Loading indicator
      
      // Should show skeleton rows
      const skeletonRows = screen.getAllByRole('row');
      expect(skeletonRows.length).toBeGreaterThan(1); // Header + skeleton rows
    });

    it('should disable interactions when loading', () => {
      const mockOnSort = jest.fn();
      render(<ResultsTable {...defaultProps} loading={true} onSort={mockOnSort} />);
      
      const sortButtons = screen.getAllByRole('button');
      sortButtons.forEach(button => {
        expect(button).toBeDisabled();
      });
    });
  });

  describe('Error States', () => {
    it('should show error state when error prop is provided', () => {
      const errorMessage = 'Failed to load results';
      render(<ResultsTable {...defaultProps} error={errorMessage} />);
      
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('should show retry button on error', () => {
      const mockOnRetry = jest.fn();
      render(<ResultsTable {...defaultProps} error="Error occurred" onRetry={mockOnRetry} />);
      
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();
    });

    it('should call onRetry when retry button is clicked', async () => {
      const user = userEvent.setup();
      const mockOnRetry = jest.fn();
      render(<ResultsTable {...defaultProps} error="Error occurred" onRetry={mockOnRetry} />);
      
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);
      
      expect(mockOnRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('Sorting Functionality', () => {
    it('should render sortable column headers', () => {
      const mockOnSort = jest.fn();
      render(<ResultsTable {...defaultProps} onSort={mockOnSort} />);
      
      // Check for sortable headers
      expect(screen.getByRole('button', { name: /sort by symbol/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sort by price/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sort by change/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sort by signal/i })).toBeInTheDocument();
    });

    it('should call onSort when column header is clicked', async () => {
      const user = userEvent.setup();
      const mockOnSort = jest.fn();
      render(<ResultsTable {...defaultProps} onSort={mockOnSort} />);
      
      const symbolHeader = screen.getByRole('button', { name: /sort by symbol/i });
      await user.click(symbolHeader);
      
      expect(mockOnSort).toHaveBeenCalledWith('symbol', 'asc');
    });

    it('should toggle sort direction on subsequent clicks', async () => {
      const user = userEvent.setup();
      const mockOnSort = jest.fn();
      render(<ResultsTable {...defaultProps} onSort={mockOnSort} />);
      
      const priceHeader = screen.getByRole('button', { name: /sort by price/i });
      
      // First click - ascending
      await user.click(priceHeader);
      expect(mockOnSort).toHaveBeenCalledWith('price', 'asc');
      
      // Second click - descending
      await user.click(priceHeader);
      expect(mockOnSort).toHaveBeenCalledWith('price', 'desc');
    });

    it('should show sort indicators on active columns', () => {
      const mockOnSort = jest.fn();
      render(<ResultsTable {...defaultProps} onSort={mockOnSort} sortConfig={{ column: 'price', direction: 'desc' }} />);
      
      // Should show descending indicator on price column
      const priceHeader = screen.getByRole('button', { name: /sort by price/i });
      expect(priceHeader).toHaveAttribute('aria-sort', 'descending');
    });
  });

  describe('Row Interactions', () => {
    it('should make rows clickable when onRowClick is provided', () => {
      const mockOnRowClick = jest.fn();
      render(<ResultsTable {...defaultProps} onRowClick={mockOnRowClick} />);
      
      const rows = screen.getAllByRole('row');
      // Skip header row
      const dataRows = rows.slice(1);
      
      dataRows.forEach(row => {
        expect(row).toHaveClass('cursor-pointer');
        expect(row).toHaveAttribute('tabindex', '0');
      });
    });

    it('should call onRowClick when row is clicked', async () => {
      const user = userEvent.setup();
      const mockOnRowClick = jest.fn();
      render(<ResultsTable {...defaultProps} onRowClick={mockOnRowClick} />);
      
      const rows = screen.getAllByRole('row');
      expect(rows.length).toBeGreaterThan(1); // Should have header + data rows
      const firstDataRow = rows[1]; // Skip header
      
      await user.click(firstDataRow);
      
      expect(mockOnRowClick).toHaveBeenCalledWith(mockResults[0]);
    });

    it('should handle keyboard navigation on clickable rows', async () => {
      const user = userEvent.setup();
      const mockOnRowClick = jest.fn();
      render(<ResultsTable {...defaultProps} onRowClick={mockOnRowClick} />);
      
      const rows = screen.getAllByRole('row');
      const firstDataRow = rows[1]; // Skip header
      
      // Focus the row using user-event for proper act() handling
      await user.click(firstDataRow);
      await user.keyboard('{Enter}');
      
      // Should be called twice - once for click, once for Enter
      expect(mockOnRowClick).toHaveBeenCalledTimes(2);
      expect(mockOnRowClick).toHaveBeenCalledWith(mockResults[0]);
    });
  });

  describe('Responsive Behavior', () => {
    it('should show compact view on mobile', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 640,
      });
      
      render(<ResultsTable {...defaultProps} />);
      
      // On mobile, some columns should be hidden
      expect(screen.queryByText('Volume')).not.toBeInTheDocument();
      expect(screen.queryByText('Company')).not.toBeInTheDocument();
    });

    it('should show horizontal scroll on very small screens', () => {
      // Mock very small viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320,
      });
      
      render(<ResultsTable {...defaultProps} />);
      
      const tableContainer = screen.getByRole('table').closest('div');
      expect(tableContainer).toHaveClass('overflow-x-auto');
    });
  });

  describe('Accessibility', () => {
    it('should have proper table structure', () => {
      render(<ResultsTable {...defaultProps} />);
      
      expect(screen.getByRole('table')).toBeInTheDocument();
      
      // Check columns (may vary based on mobile/desktop)
      const columnHeaders = screen.getAllByRole('columnheader');
      expect(columnHeaders.length).toBeGreaterThanOrEqual(5); // At least 5 columns
      
      const rows = screen.getAllByRole('row');
      expect(rows.length).toBe(5); // Header + 4 data rows
    });

    it('should have proper ARIA labels', () => {
      render(<ResultsTable {...defaultProps} />);
      
      const table = screen.getByRole('table');
      expect(table).toHaveAttribute('aria-label', 'Scan results');
    });

    it('should announce sort state to screen readers', () => {
      const mockOnSort = jest.fn();
      render(<ResultsTable {...defaultProps} onSort={mockOnSort} sortConfig={{ column: 'symbol', direction: 'asc' }} />);
      
      const symbolHeader = screen.getByRole('button', { name: /sort by symbol/i });
      expect(symbolHeader).toHaveAttribute('aria-sort', 'ascending');
    });

    it('should provide keyboard navigation for interactive elements', async () => {
      const user = userEvent.setup();
      const mockOnSort = jest.fn();
      render(<ResultsTable {...defaultProps} onSort={mockOnSort} />);
      
      const firstSortButton = screen.getByRole('button', { name: /sort by symbol/i });
      firstSortButton.focus();
      
      await user.keyboard('{Tab}');
      
      // Should move to next sortable header
      const nextButton = screen.getByRole('button', { name: /sort by company/i });
      expect(nextButton).toHaveFocus();
    });
  });

  describe('Data Formatting', () => {
    it('should format large numbers correctly', () => {
      const largeNumberResult: ScanResult = {
        ...mockResults[0],
        volume: 123456789,
        price: 12345.67,
      };
      
      render(<ResultsTable {...defaultProps} results={[largeNumberResult]} />);
      
      expect(screen.getByText('$12,345.67')).toBeInTheDocument();
      expect(screen.getByText('123.5M')).toBeInTheDocument();
    });

    it('should handle zero and negative values', () => {
      const edgeCaseResult: ScanResult = {
        ...mockResults[0],
        change: 0,
        changePercent: 0,
        volume: 0,
      };
      
      render(<ResultsTable {...defaultProps} results={[edgeCaseResult]} />);
      
      expect(screen.getByText('+$0.00 (+0.00%)')).toBeInTheDocument();
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('should handle large datasets efficiently', () => {
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        ...mockResults[0],
        symbol: `STOCK${i}`,
        companyName: `Company ${i}`,
      }));
      
      const { container } = render(<ResultsTable {...defaultProps} results={largeDataset} />);
      
      // Should render efficiently without performance issues
      const rows = container.querySelectorAll('tbody tr');
      expect(rows.length).toBe(1000);
    });

    it('should support virtual scrolling for very large datasets', () => {
      const hugeDataset = Array.from({ length: 10000 }, (_, i) => ({
        ...mockResults[0],
        symbol: `STOCK${i}`,
        companyName: `Company ${i}`,
      }));
      
      render(<ResultsTable {...defaultProps} results={hugeDataset} virtualScrolling={true} />);
      
      // Should only render visible rows
      const visibleRows = screen.getAllByRole('row');
      expect(visibleRows.length).toBeLessThan(100); // Much less than total
    });
  });
});