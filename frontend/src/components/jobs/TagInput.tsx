import * as React from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

interface TagInputProps {
  label: string
  values: string[]
  onChange: (values: string[]) => void
  placeholder?: string
  maxTags?: number
  className?: string
}

function TagInput({
  label,
  values,
  onChange,
  placeholder = "Type and press Enter to add...",
  maxTags,
  className,
}: TagInputProps) {
  const [inputValue, setInputValue] = React.useState("")
  const [error, setError] = React.useState("")
  const inputRef = React.useRef<HTMLInputElement>(null)

  const addTag = (tag: string) => {
    const trimmed = tag.trim()
    if (!trimmed) return

    // Check for duplicates
    if (values.includes(trimmed)) {
      setError(`"${trimmed}" is already added`)
      setTimeout(() => setError(""), 3000)
      return
    }

    // Check max tags limit
    if (maxTags && values.length >= maxTags) {
      setError(`Maximum ${maxTags} tags allowed`)
      setTimeout(() => setError(""), 3000)
      return
    }

    onChange([...values, trimmed])
    setInputValue("")
    setError("")
  }

  const removeTag = (index: number) => {
    const newValues = values.filter((_, i) => i !== index)
    onChange(newValues)
    setError("")
  }

  const removeLastTag = () => {
    if (values.length > 0) {
      removeTag(values.length - 1)
    }
  }

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    switch (e.key) {
      case "Enter":
        e.preventDefault()
        addTag(inputValue)
        break
      case "Backspace":
        if (!inputValue && values.length > 0) {
          removeLastTag()
        }
        break
      case "Escape":
        setInputValue("")
        setError("")
        break
    }
  }

  return (
    <div className={cn("space-y-2", className)}>
      <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
        {label}
      </label>
      
      <div className="space-y-2">
        <div className="flex flex-wrap gap-1 p-2 min-h-[2.5rem] border border-input rounded-lg bg-transparent focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50">
          {values.map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 bg-secondary text-secondary-foreground px-2 py-1 rounded-md text-sm"
            >
              <span>{tag}</span>
              <button
                type="button"
                onClick={() => removeTag(index)}
                className="inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-secondary-foreground/20 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                aria-label={`Remove ${tag}`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder={values.length === 0 ? placeholder : ""}
            className="flex-1 min-w-[120px] bg-transparent text-base outline-none placeholder:text-muted-foreground md:text-sm"
            disabled={!!(maxTags && values.length >= maxTags)}
          />
        </div>
        
        {error && (
          <div 
            className="text-sm text-destructive" 
            role="alert"
            aria-live="polite"
          >
            {error}
          </div>
        )}
      </div>
    </div>
  )
}

export { TagInput }
export type { TagInputProps }