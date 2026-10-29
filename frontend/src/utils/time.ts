function toDate(input?: string | number | Date | null): Date | null {
  if (input === null || input === undefined || input === '') {
    return null;
  }
  try {
    if (input instanceof Date) {
      return isNaN(input.getTime()) ? null : input;
    }
    if (typeof input === 'number') {
      // If looks like seconds
      if (input < 1000000000000) {
        const d = new Date(input * 1000);
        return isNaN(d.getTime()) ? null : d;
      }
      const d = new Date(input);
      return isNaN(d.getTime()) ? null : d;
    }
    if (typeof input === 'string') {
      // If no timezone info, assume UTC (common from backend)
      let s = input.trim();
      // ISO format without Z or offset
      if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(s)) {
        s = s.replace(' ', 'T') + 'Z';
      } else if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?[+-]\d{2}:?\d{2}$/.test(s)) {
        // has offset, keep as-is
      } else if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?Z$/.test(s)) {
        // already UTC
      } else if (/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(s.replace('Z', ''))) {
        s = s.replace('Z', '') + 'Z';
      }
      // If ends with space and no TZ, assume UTC
      if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(s) && !/[Zz]|[+-]\d{2}/.test(s)) {
        s = s.replace(' ', 'T') + 'Z';
      }
      const d = new Date(s);
      if (isNaN(d.getTime())) {
        // try original
        const d2 = new Date(input);
        return isNaN(d2.getTime()) ? null : d2;
      }
      return d;
    }
    return null;
  } catch {
    return null;
  }
}

export function formatToIST(
  input?: string | number | Date | null,
  options?: Intl.DateTimeFormatOptions
): string {
  const date = toDate(input);
  if (!date) {
    return input === null || input === undefined || input === '' ? '—' : String(input);
  }

  const defaultOptions: Intl.DateTimeFormatOptions = {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  };

  return date.toLocaleString('en-IN', { ...defaultOptions, ...options });
}

export function formatDateIST(input?: string | number | Date | null): string {
  const date = toDate(input);
  if (!date) {
    return input === null || input === undefined || input === '' ? '—' : String(input);
  }

  return date.toLocaleDateString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function formatTimeIST(input?: string | number | Date | null): string {
  const date = toDate(input);
  if (!date) {
    return input === null || input === undefined || input === '' ? '—' : String(input);
  }

  return date.toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
}

export function formatHourIST(input?: string | number | Date | null): string {
  const date = toDate(input);
  if (!date) {
    return input === null || input === undefined || input === '' ? '—' : String(input);
  }

  return date.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
}
