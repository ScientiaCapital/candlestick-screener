import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PatternSelector } from '@/app/components/PatternSelector';
import { Pattern } from '@/app/lib/types';

// Test data
const mockPatterns: Pattern[] = [
  { name: 'doji', displayName: 'Doji', type: 'neutral', description: 'Indecision pattern' },
  { name: 'hammer', displayName: 'Hammer', type: 'bullish', description: 'Bullish reversal' },
  { name: 'shooting_star', displayName: 'Shooting Star', type: 'bearish', description: 'Bearish reversal' },
  { name: 'marubozu', displayName: 'Marubozu', type: 'bullish', description: 'Strong trend' },
];

const defaultProps = {
  patterns: mockPatterns,
  selectedPattern: null,
  onPatternSelect: jest.fn(),
};

describe('PatternSelector Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the pattern selector dropdown', () => {
      render(<PatternSelector {...defaultProps} />);
      
      expect(screen.getByRole('combobox', { name: /select pattern/i })).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Select a candlestick pattern')).toBeInTheDocument();
    });

    it('should render all patterns in the dropdown when opened', async () => {
      const user = userEvent.setup();
      render(<PatternSelector {...defaultProps} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      await user.click(selector);
      
      mockPatterns.forEach(pattern => {
        expect(screen.getByText(pattern.displayName)).toBeInTheDocument();
      });
    });

    it('should display pattern types with appropriate indicators', async () => {
      const user = userEvent.setup();
      render(<PatternSelector {...defaultProps} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      await user.click(selector);
      
      // Check for type indicators (assuming we use colors or icons)
      expect(screen.getByText('Hammer')).toBeInTheDocument();
      expect(screen.getByText('Shooting Star')).toBeInTheDocument();
      expect(screen.getByText('Doji')).toBeInTheDocument();
    });

    it('should show selected pattern when selectedPattern prop is provided', () => {
      render(<PatternSelector {...defaultProps} selectedPattern="hammer" />);
      
      expect(screen.getByDisplayValue('Hammer')).toBeInTheDocument();
    });
  });

  describe('Interaction', () => {
    it('should call onPatternSelect when a pattern is selected', async () => {
      const user = userEvent.setup();
      const mockOnPatternSelect = jest.fn();
      
      render(<PatternSelector {...defaultProps} onPatternSelect={mockOnPatternSelect} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      await user.click(selector);
      
      const hammerOption = screen.getByText('Hammer');
      await user.click(hammerOption);
      
      expect(mockOnPatternSelect).toHaveBeenCalledWith('hammer');
    });

    it('should filter patterns when typing in search', async () => {
      const user = userEvent.setup();
      render(<PatternSelector {...defaultProps} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      await user.click(selector);
      await user.type(selector, 'ham');
      
      await waitFor(() => {
        expect(screen.getByText('Hammer')).toBeInTheDocument();
        expect(screen.queryByText('Doji')).not.toBeInTheDocument();
      });
    });

    it('should show no results message when search yields no matches', async () => {
      const user = userEvent.setup();
      render(<PatternSelector {...defaultProps} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      await user.click(selector);
      await user.type(selector, 'nonexistent');
      
      await waitFor(() => {
        expect(screen.getByText(/no patterns found/i)).toBeInTheDocument();
      });
    });

    it('should clear selection when clear button is clicked', async () => {
      const user = userEvent.setup();
      const mockOnPatternSelect = jest.fn();
      
      render(<PatternSelector {...defaultProps} selectedPattern="hammer" onPatternSelect={mockOnPatternSelect} />);
      
      const clearButton = screen.getByRole('button', { name: /clear selection/i });
      await user.click(clearButton);
      
      expect(mockOnPatternSelect).toHaveBeenCalledWith('');
    });
  });

  describe('Loading and Error States', () => {
    it('should show loading state when loading prop is true', () => {
      render(<PatternSelector {...defaultProps} loading={true} />);
      
      expect(screen.getByPlaceholderText(/loading patterns/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/select pattern/i)).toBeDisabled();
    });

    it('should show error state when error prop is provided', () => {
      const errorMessage = 'Failed to load patterns';
      render(<PatternSelector {...defaultProps} error={errorMessage} />);
      
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByLabelText(/select pattern/i)).toBeDisabled();
    });

    it('should disable selector when patterns array is empty', () => {
      render(<PatternSelector {...defaultProps} patterns={[]} />);
      
      expect(screen.getByLabelText(/select pattern/i)).toBeDisabled();
      expect(screen.getByPlaceholderText(/no patterns available/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<PatternSelector {...defaultProps} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      expect(selector).toHaveAttribute('aria-haspopup', 'listbox');
      expect(selector).toHaveAttribute('aria-expanded', 'false');
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      const mockOnPatternSelect = jest.fn();
      
      render(<PatternSelector {...defaultProps} onPatternSelect={mockOnPatternSelect} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      
      // Focus and open dropdown with Enter
      await user.click(selector);
      await user.keyboard('{Enter}');
      
      // Navigate with arrow keys
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{Enter}');
      
      expect(mockOnPatternSelect).toHaveBeenCalled();
    });

    it('should close dropdown on Escape key', async () => {
      const user = userEvent.setup();
      render(<PatternSelector {...defaultProps} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      await user.click(selector);
      
      expect(selector).toHaveAttribute('aria-expanded', 'true');
      
      await user.keyboard('{Escape}');
      
      expect(selector).toHaveAttribute('aria-expanded', 'false');
    });
  });

  describe('Pattern Categories', () => {
    it('should group patterns by type when groupByType prop is true', async () => {
      const user = userEvent.setup();
      render(<PatternSelector {...defaultProps} groupByType={true} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      await user.click(selector);
      
      // Check for group headers
      expect(screen.getByText('Bullish Patterns')).toBeInTheDocument();
      expect(screen.getByText('Bearish Patterns')).toBeInTheDocument();
      expect(screen.getByText('Neutral Patterns')).toBeInTheDocument();
    });

    it('should show pattern descriptions when showDescriptions prop is true', async () => {
      const user = userEvent.setup();
      render(<PatternSelector {...defaultProps} showDescriptions={true} />);
      
      const selector = screen.getByRole('combobox', { name: /select pattern/i });
      await user.click(selector);
      
      mockPatterns.forEach(pattern => {
        if (pattern.description) {
          expect(screen.getByText(pattern.description)).toBeInTheDocument();
        }
      });
    });
  });
});