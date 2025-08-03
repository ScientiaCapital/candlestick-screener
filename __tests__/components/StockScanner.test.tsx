import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { StockScanner } from '../../app/components/StockScanner';
import { ScanRequest } from '../../app/lib/types';

// Mock the PatternSelector component to avoid circular dependencies
jest.mock('../../app/components/PatternSelector', () => ({
  PatternSelector: ({ onPatternSelect, selectedPattern }: any) => (
    <div data-testid="pattern-selector">
      <button onClick={() => onPatternSelect('hammer')}>Select Hammer</button>
      <span>Selected: {selectedPattern || 'None'}</span>
    </div>
  ),
}));

const defaultProps = {
  onScan: jest.fn(),
};

describe('StockScanner Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the stock scanner form', () => {
      render(<StockScanner {...defaultProps} />);
      
      expect(screen.getByRole('heading', { name: /stock scanner/i })).toBeInTheDocument();
      expect(screen.getByTestId('pattern-selector')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /scan stocks/i })).toBeInTheDocument();
    });

    it('should render filters section', () => {
      render(<StockScanner {...defaultProps} />);
      
      expect(screen.getByLabelText(/minimum volume/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/minimum price/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/maximum price/i)).toBeInTheDocument();
    });

    it('should render timeframe selector', () => {
      render(<StockScanner {...defaultProps} />);
      
      expect(screen.getByLabelText(/timeframe/i)).toBeInTheDocument();
      const timeframeSelect = screen.getByLabelText(/timeframe/i);
      expect(timeframeSelect).toHaveValue('1d'); // Default timeframe
    });

    it('should show advanced filters toggle', () => {
      render(<StockScanner {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: /advanced filters/i })).toBeInTheDocument();
    });
  });

  describe('Pattern Selection', () => {
    it('should handle pattern selection', async () => {
      const user = userEvent.setup();
      render(<StockScanner {...defaultProps} />);
      
      const selectButton = screen.getByText('Select Hammer');
      await user.click(selectButton);
      
      expect(screen.getByText('Selected: hammer')).toBeInTheDocument();
    });

    it('should enable scan button when pattern is selected', async () => {
      const user = userEvent.setup();
      render(<StockScanner {...defaultProps} />);
      
      const scanButton = screen.getByRole('button', { name: /scan stocks/i });
      expect(scanButton).toBeDisabled();
      
      const selectButton = screen.getByText('Select Hammer');
      await user.click(selectButton);
      
      // Wait for state update
      await waitFor(() => {
        expect(screen.getByText('Selected: hammer')).toBeInTheDocument();
      });
      
      await waitFor(() => {
        expect(scanButton).toBeEnabled();
      });
    });
  });

  describe('Filter Controls', () => {
    it('should update minimum volume filter', async () => {
      const user = userEvent.setup();
      render(<StockScanner {...defaultProps} />);
      
      const volumeInput = screen.getByLabelText(/minimum volume/i);
      await user.clear(volumeInput);
      await user.type(volumeInput, '1000000');
      
      expect(volumeInput).toHaveValue(1000000);
    });

    it('should update price range filters', async () => {
      const user = userEvent.setup();
      render(<StockScanner {...defaultProps} />);
      
      const minPriceInput = screen.getByLabelText(/minimum price/i);
      const maxPriceInput = screen.getByLabelText(/maximum price/i);
      
      await user.clear(minPriceInput);
      await user.type(minPriceInput, '10');
      await user.clear(maxPriceInput);
      await user.type(maxPriceInput, '100');
      
      expect(minPriceInput).toHaveValue(10);
      expect(maxPriceInput).toHaveValue(100);
    });

    it('should update timeframe selection', async () => {
      const user = userEvent.setup();
      render(<StockScanner {...defaultProps} />);
      
      const timeframeSelect = screen.getByLabelText(/timeframe/i);
      await user.selectOptions(timeframeSelect, '1h');
      
      expect(timeframeSelect).toHaveValue('1h');
    });

    it('should toggle advanced filters', async () => {
      const user = userEvent.setup();
      render(<StockScanner {...defaultProps} />);
      
      const advancedToggle = screen.getByRole('button', { name: /advanced filters/i });
      
      // Advanced filters should be hidden initially
      expect(screen.queryByLabelText(/pattern type filter/i)).not.toBeInTheDocument();
      
      await user.click(advancedToggle);
      
      // Advanced filters should now be visible
      expect(screen.getByLabelText(/pattern type filter/i)).toBeInTheDocument();
    });
  });

  describe('Scan Functionality', () => {
    it('should call onScan with correct parameters when scan button is clicked', async () => {
      const user = userEvent.setup();
      const mockOnScan = jest.fn();
      render(<StockScanner {...defaultProps} onScan={mockOnScan} />);
      
      // Select a pattern
      const selectButton = screen.getByText('Select Hammer');
      await user.click(selectButton);
      
      // Set filters
      const volumeInput = screen.getByLabelText(/minimum volume/i);
      await user.clear(volumeInput);
      await user.type(volumeInput, '500000');
      
      const minPriceInput = screen.getByLabelText(/minimum price/i);
      await user.clear(minPriceInput);
      await user.type(minPriceInput, '5');
      
      // Click scan
      const scanButton = screen.getByRole('button', { name: /scan stocks/i });
      await user.click(scanButton);
      
      expect(mockOnScan).toHaveBeenCalledWith({
        pattern: 'hammer',
        timeframe: '1d',
        minVolume: 500000,
        minPrice: 5,
        maxPrice: null,
      });
    });

    it('should not call onScan when no pattern is selected', async () => {
      const user = userEvent.setup();
      const mockOnScan = jest.fn();
      render(<StockScanner {...defaultProps} onScan={mockOnScan} />);
      
      const scanButton = screen.getByRole('button', { name: /scan stocks/i });
      await user.click(scanButton);
      
      expect(mockOnScan).not.toHaveBeenCalled();
    });

    it('should show reset button after successful scan', async () => {
      const user = userEvent.setup();
      const mockOnScan = jest.fn();
      render(<StockScanner {...defaultProps} onScan={mockOnScan} loading={false} />);
      
      // Select pattern and scan
      const selectButton = screen.getByText('Select Hammer');
      await user.click(selectButton);
      
      const scanButton = screen.getByRole('button', { name: /scan stocks/i });
      await user.click(scanButton);
      
      // Check if reset button appears after scan
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
      });
    });
  });

  describe('Loading and Error States', () => {
    it('should show loading state when loading prop is true', () => {
      render(<StockScanner {...defaultProps} loading={true} />);
      
      const scanButton = screen.getByRole('button', { name: /scanning/i });
      expect(scanButton).toBeDisabled();
      expect(screen.getByText(/scanning for patterns/i)).toBeInTheDocument();
    });

    it('should show error state when error prop is provided', () => {
      const errorMessage = 'Failed to scan stocks';
      render(<StockScanner {...defaultProps} error={errorMessage} />);
      
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('should disable form controls when loading', () => {
      render(<StockScanner {...defaultProps} loading={true} />);
      
      expect(screen.getByLabelText(/minimum volume/i)).toBeDisabled();
      expect(screen.getByLabelText(/minimum price/i)).toBeDisabled();
      expect(screen.getByLabelText(/maximum price/i)).toBeDisabled();
      expect(screen.getByLabelText(/timeframe/i)).toBeDisabled();
    });
  });

  describe('Form Validation', () => {
    it('should validate that minimum price is less than maximum price', async () => {
      const user = userEvent.setup();
      render(<StockScanner {...defaultProps} />);
      
      // First select a pattern to enable scanning
      const selectButton = screen.getByText('Select Hammer');
      await user.click(selectButton);
      
      const minPriceInput = screen.getByLabelText(/minimum price/i);
      const maxPriceInput = screen.getByLabelText(/maximum price/i);
      
      await user.clear(minPriceInput);
      await user.type(minPriceInput, '100');
      await user.clear(maxPriceInput);
      await user.type(maxPriceInput, '50');
      
      // Try to scan - this should trigger validation
      const scanButton = screen.getByRole('button', { name: /scan stocks/i });
      await user.click(scanButton);
      
      expect(screen.getByText(/minimum price must be less than maximum price/i)).toBeInTheDocument();
    });

    it('should validate that volume is a positive number', async () => {
      const user = userEvent.setup();
      render(<StockScanner {...defaultProps} />);
      
      const volumeInput = screen.getByLabelText(/minimum volume/i);
      await user.clear(volumeInput);
      await user.type(volumeInput, '-1000');
      
      await user.tab(); // Trigger blur event for validation
      
      expect(screen.getByText(/volume must be a positive number/i)).toBeInTheDocument();
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('should trigger scan when Enter key is pressed', async () => {
      const user = userEvent.setup();
      const mockOnScan = jest.fn();
      render(<StockScanner {...defaultProps} onScan={mockOnScan} />);
      
      // Select a pattern first
      const selectButton = screen.getByText('Select Hammer');
      await user.click(selectButton);
      
      // Press Enter on the form
      const form = screen.getByRole('form');
      await user.type(form, '{enter}');
      
      expect(mockOnScan).toHaveBeenCalled();
    });

    it('should support Ctrl+R to reset form', async () => {
      const user = userEvent.setup();
      render(<StockScanner {...defaultProps} />);
      
      // Set some values
      const volumeInput = screen.getByLabelText(/minimum volume/i);
      await user.type(volumeInput, '1000');
      
      // Press Ctrl+R
      await user.keyboard('{Control>}r{/Control}');
      
      expect(volumeInput).toHaveValue(null);
    });
  });

  describe('Accessibility', () => {
    it('should have proper form structure and labels', () => {
      render(<StockScanner {...defaultProps} />);
      
      expect(screen.getByRole('form')).toBeInTheDocument();
      
      // Check for input fields (they might be spinbutton due to type="number")
      const volumeInput = screen.getByLabelText(/minimum volume/i);
      const minPriceInput = screen.getByLabelText(/minimum price/i);
      const maxPriceInput = screen.getByLabelText(/maximum price/i);
      const timeframeSelect = screen.getByLabelText(/timeframe/i);
      
      expect(volumeInput).toBeInTheDocument();
      expect(minPriceInput).toBeInTheDocument();
      expect(maxPriceInput).toBeInTheDocument();
      expect(timeframeSelect).toBeInTheDocument();
    });

    it('should announce loading state to screen readers', () => {
      render(<StockScanner {...defaultProps} loading={true} />);
      
      expect(screen.getByLabelText(/scanning in progress/i)).toBeInTheDocument();
    });

    it('should have proper error announcement', () => {
      const errorMessage = 'Network error occurred';
      render(<StockScanner {...defaultProps} error={errorMessage} />);
      
      const errorElement = screen.getByRole('alert');
      expect(errorElement).toHaveTextContent(errorMessage);
    });
  });

  describe('Responsive Behavior', () => {
    it('should collapse filters on mobile view', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320,
      });
      
      render(<StockScanner {...defaultProps} />);
      
      // On mobile, filters should be collapsible
      expect(screen.getByRole('button', { name: /show filters/i })).toBeInTheDocument();
    });
  });
});