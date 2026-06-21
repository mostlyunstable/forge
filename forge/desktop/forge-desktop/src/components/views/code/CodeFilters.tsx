import { useState } from 'react';
import { Search } from 'lucide-react';

interface CodeFiltersProps {
  onSearch: (query: string) => void;
}

export function CodeFilters({ onSearch }: CodeFiltersProps) {
  const [query, setQuery] = useState('');

  return (
    <div className="border-b border-[var(--color-border-subtle)] px-2 py-2">
      <div className="relative">
        <Search className="absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-[var(--color-text-faint)]" />
        <input
          type="text"
          placeholder="Search files..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            onSearch(e.target.value);
          }}
          className="input pl-7 py-1.5 text-[11px] placeholder:text-[var(--color-text-faint)]"
        />
      </div>
    </div>
  );
}
