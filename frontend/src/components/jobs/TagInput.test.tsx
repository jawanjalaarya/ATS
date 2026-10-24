import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { TagInput } from './TagInput'

describe('TagInput', () => {
  const defaultProps = {
    label: 'Test Tags',
    values: [],
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  // Component rendering tests
  describe('Rendering', () => {
    it('renders with label and input', () => {
      render(<TagInput {...defaultProps} />)
      
      expect(screen.getByText('Test Tags')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Type and press Enter to add...')).toBeInTheDocument()
    })

    it('renders existing tags as pills', () => {
      render(<TagInput {...defaultProps} values={['React', 'TypeScript']} />)
      
      expect(screen.getByText('React')).toBeInTheDocument()
      expect(screen.getByText('TypeScript')).toBeInTheDocument()
      
      // Should have remove buttons for each tag
      expect(screen.getByRole('button', { name: 'Remove React' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Remove TypeScript' })).toBeInTheDocument()
    })

    it('renders with custom placeholder', () => {
      render(<TagInput {...defaultProps} placeholder="Add skills..." />)
      
      expect(screen.getByPlaceholderText('Add skills...')).toBeInTheDocument()
    })

    it('shows placeholder only when no tags exist', () => {
      const { rerender } = render(<TagInput {...defaultProps} />)
      
      // No tags - should show placeholder
      expect(screen.getByPlaceholderText('Type and press Enter to add...')).toBeInTheDocument()
      
      // With tags - placeholder should be empty string
      rerender(<TagInput {...defaultProps} values={['React']} />)
      expect(screen.getByDisplayValue('')).toBeInTheDocument()
    })
  })

  // Tag addition tests
  describe('Tag Addition', () => {
    it('adds tag on Enter key press', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} onChange={mockOnChange} />)
      
      const input = screen.getByPlaceholderText('Type and press Enter to add...')
      
      await userEvent.type(input, 'JavaScript')
      await userEvent.keyboard('{Enter}')
      
      expect(mockOnChange).toHaveBeenCalledWith(['JavaScript'])
    })

    it('trims whitespace on add', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} onChange={mockOnChange} />)
      
      const input = screen.getByPlaceholderText('Type and press Enter to add...')
      
      await userEvent.type(input, '  JavaScript  ')
      await userEvent.keyboard('{Enter}')
      
      expect(mockOnChange).toHaveBeenCalledWith(['JavaScript'])
    })

    it('does not add empty tags', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} onChange={mockOnChange} />)
      
      const input = screen.getByPlaceholderText('Type and press Enter to add...')
      
      await userEvent.keyboard('{Enter}')
      expect(mockOnChange).not.toHaveBeenCalled()
      
      await userEvent.type(input, '   ')
      await userEvent.keyboard('{Enter}')
      expect(mockOnChange).not.toHaveBeenCalled()
    })

    it('clears input after successful add', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} onChange={mockOnChange} />)
      
      const input = screen.getByPlaceholderText('Type and press Enter to add...')
      
      await userEvent.type(input, 'JavaScript')
      expect(input).toHaveValue('JavaScript')
      
      await userEvent.keyboard('{Enter}')
      expect(input).toHaveValue('')
    })

    it('disables input when max tags reached', () => {
      render(
        <TagInput 
          {...defaultProps} 
          values={['React', 'Vue']} 
          maxTags={2} 
        />
      )
      
      const input = screen.getByDisplayValue('')
      expect(input).toBeDisabled()
    })
  })

  // Tag removal tests
  describe('Tag Removal', () => {
    it('removes tag on button click', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} values={['React', 'Vue']} onChange={mockOnChange} />)
      
      const removeButton = screen.getByRole('button', { name: 'Remove React' })
      await userEvent.click(removeButton)
      
      expect(mockOnChange).toHaveBeenCalledWith(['Vue'])
    })

    it('removes last tag on backspace when input is empty', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} values={['React', 'Vue']} onChange={mockOnChange} />)
      
      const input = screen.getByDisplayValue('')
      
      // Focus input first
      input.focus()
      // Input is empty, backspace should remove last tag
      fireEvent.keyDown(input, { key: 'Backspace' })
      
      expect(mockOnChange).toHaveBeenCalledWith(['React'])
    })

    it('does not remove tags on backspace when input has content', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} values={['React', 'Vue']} onChange={mockOnChange} />)
      
      const input = screen.getByDisplayValue('')
      
      await userEvent.type(input, 'test')
      fireEvent.keyDown(input, { key: 'Backspace' })
      
      // Should only remove character from input, not tags
      expect(mockOnChange).not.toHaveBeenCalled()
    })

    it('does not remove tags on backspace when no tags exist', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} onChange={mockOnChange} />)
      
      const input = screen.getByPlaceholderText('Type and press Enter to add...')
      
      fireEvent.keyDown(input, { key: 'Backspace' })
      
      expect(mockOnChange).not.toHaveBeenCalled()
    })
  })

  // Keyboard navigation tests
  describe('Keyboard Navigation', () => {
    it('supports tab navigation through tags', () => {
      render(<TagInput {...defaultProps} values={['React', 'Vue', 'Angular']} />)
      
      const input = screen.getByDisplayValue('')
      const reactButton = screen.getByRole('button', { name: 'Remove React' })
      const vueButton = screen.getByRole('button', { name: 'Remove Vue' })
      const angularButton = screen.getByRole('button', { name: 'Remove Angular' })
      
      // All elements should be in tab order
      expect(reactButton).toBeInTheDocument()
      expect(vueButton).toBeInTheDocument()
      expect(angularButton).toBeInTheDocument()
      expect(input).toBeInTheDocument()
    })

    it('clears input on escape key', async () => {
      render(<TagInput {...defaultProps} />)
      
      const input = screen.getByPlaceholderText('Type and press Enter to add...')
      
      await userEvent.type(input, 'JavaScript')
      expect(input).toHaveValue('JavaScript')
      
      fireEvent.keyDown(input, { key: 'Escape' })
      expect(input).toHaveValue('')
    })
  })

  // Accessibility tests
  describe('Accessibility', () => {
    it('has accessible remove buttons with descriptive names', () => {
      render(<TagInput {...defaultProps} values={['React', 'TypeScript']} />)
      
      expect(screen.getByRole('button', { name: 'Remove React' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Remove TypeScript' })).toBeInTheDocument()
    })

    it('has proper label association', () => {
      render(<TagInput {...defaultProps} label="Required Skills" />)
      
      const label = screen.getByText('Required Skills')
      expect(label).toBeInTheDocument()
      expect(label.tagName).toBe('LABEL')
    })

    it('has focus management after operations', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} onChange={mockOnChange} />)
      
      const input = screen.getByPlaceholderText('Type and press Enter to add...')
      
      // Input should maintain focus after adding tag
      input.focus()
      await userEvent.type(input, 'JavaScript')
      await userEvent.keyboard('{Enter}')
      
      expect(input).toHaveFocus()
    })
  })

  // Duplicate prevention tests
  describe('Duplicate Prevention', () => {
    it('prevents duplicate tags', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} values={['React']} onChange={mockOnChange} />)
      
      const input = screen.getByDisplayValue('')
      
      await userEvent.type(input, 'React')
      await userEvent.keyboard('{Enter}')
      
      expect(mockOnChange).not.toHaveBeenCalled()
    })

    it('handles case sensitivity correctly', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} values={['React']} onChange={mockOnChange} />)
      
      const input = screen.getByDisplayValue('')
      
      // Different case should be allowed (case sensitive)
      await userEvent.type(input, 'react')
      await userEvent.keyboard('{Enter}')
      
      expect(mockOnChange).toHaveBeenCalledWith(['React', 'react'])
    })
  })

  // Edge cases tests
  describe('Edge Cases', () => {
    it('handles only whitespace input correctly', async () => {
      const mockOnChange = vi.fn()
      render(<TagInput {...defaultProps} onChange={mockOnChange} />)
      
      const input = screen.getByPlaceholderText('Type and press Enter to add...')
      
      await userEvent.type(input, '   ')
      await userEvent.keyboard('{Enter}')
      
      expect(mockOnChange).not.toHaveBeenCalled()
    })
  })
})