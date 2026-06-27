import { describe, it, expect } from 'vitest';
import { cn } from '@/lib/utils';

describe('cn', () => {
  it('merges class names correctly', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('handles conditional classes', () => {
    expect(cn('foo', false && 'bar', 'baz')).toBe('foo baz');
    expect(cn('foo', true && 'bar', 'baz')).toBe('foo bar baz');
    expect(cn('foo', null && 'bar', 'baz')).toBe('foo baz');
    expect(cn('foo', undefined && 'bar', 'baz')).toBe('foo baz');
  });

  it('resolves Tailwind conflicts (last wins)', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4');
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
    expect(cn('m-1', 'm-2', 'm-3')).toBe('m-3');
    expect(cn('flex', 'block')).toBe('block');
  });

  it('handles undefined, null, and empty inputs', () => {
    expect(cn(undefined)).toBe('');
    expect(cn(null)).toBe('');
    expect(cn('')).toBe('');
    expect(cn(undefined, null, '')).toBe('');
  });

  it('returns empty string for no inputs', () => {
    expect(cn()).toBe('');
  });

  it('handles mixed valid and empty inputs', () => {
    expect(cn('foo', '', 'bar')).toBe('foo bar');
    expect(cn('foo', undefined, null, '', 'bar')).toBe('foo bar');
  });

  it('handles arrays as input', () => {
    expect(cn(['foo', 'bar'])).toBe('foo bar');
    expect(cn(['foo', 'bar'], 'baz')).toBe('foo bar baz');
  });

  it('handles objects as input', () => {
    expect(cn({ foo: true, bar: false })).toBe('foo');
    expect(cn({ foo: true, bar: true })).toBe('foo bar');
    expect(cn({ 'p-2': true, 'p-4': false })).toBe('p-2');
    expect(cn({ 'p-2': true, 'p-4': true })).toBe('p-4');
  });
});
