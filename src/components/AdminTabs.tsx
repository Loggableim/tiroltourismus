import type { ReactNode } from 'react';

export interface AdminTabItem {
  value: string;
  label: ReactNode;
}

interface Props {
  items: AdminTabItem[];
  active: string;
  onChange: (value: string) => void;
  className?: string;
}

export default function AdminTabs({ items, active, onChange, className = '' }: Props) {
  return (
    <div className={`admin-tabs${className ? ` ${className}` : ''}`}>
      {items.map((item) => (
        <button
          key={item.value}
          type="button"
          onClick={() => onChange(item.value)}
          className={`admin-tab${active === item.value ? ' active' : ''}`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
