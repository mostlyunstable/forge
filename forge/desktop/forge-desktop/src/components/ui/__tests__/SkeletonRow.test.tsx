import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SkeletonRow } from '../SkeletonRow';

describe('SkeletonRow', () => {
  it('renders correct number of skeleton rows (default 1)', () => {
    const { container } = render(<SkeletonRow />);
    const rows = container.querySelectorAll('.h-\\[32px\\]');
    expect(rows).toHaveLength(1);
  });

  it('renders correct number with custom lines prop', () => {
    const { container } = render(<SkeletonRow lines={5} />);
    const rows = container.querySelectorAll('.h-\\[32px\\]');
    expect(rows).toHaveLength(5);
  });

  it('renders with lines=3', () => {
    const { container } = render(<SkeletonRow lines={3} />);
    const rows = container.querySelectorAll('.h-\\[32px\\]');
    expect(rows).toHaveLength(3);
  });

  it('applies loading animation classes', () => {
    const { container } = render(<SkeletonRow />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('space-y-[4px]');

    const row = wrapper.querySelector('div');
    expect(row).toHaveClass('h-[32px]', 'rounded-[4px]', 'bg-[var(--color-bg-elevated)]');
  });

  it('applies decreasing opacity to rows', () => {
    const { container } = render(<SkeletonRow lines={3} />);
    const rows = container.querySelectorAll('.space-y-\\[4px\\] > div');

    expect(rows[0]).toHaveStyle({ opacity: 1 });
    expect(rows[1]).toHaveStyle({ opacity: 0.85 });
    expect(rows[2]).toHaveStyle({ opacity: 0.7 });
  });
});
