import React, { useState, useEffect, useCallback } from 'react';
import { FlowFilters } from '../components/flows/FlowFilters';
import { FlowTable } from '../components/flows/FlowTable';
import { Pagination } from '../components/ui/Pagination';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { getFlows } from '../services/api';
import type { Flow } from '../types';

export const FlowsPage: React.FC = () => {
  const [flows, setFlows] = useState<Flow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [srcIp, setSrcIp] = useState('');
  const [dstIp, setDstIp] = useState('');
  const [protocol, setProtocol] = useState('');
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endDate, setEndDate] = useState('');
  const [endTime, setEndTime] = useState('');
  const [skip, setSkip] = useState(0);
  const limit = 25;

  const buildIso = (date: string, time: string) => {
    if (!date) return undefined;
    const t = time || '00:00';
    // datetime-local style or just date+time
    const iso = new Date(`${date}T${t}`);
    if (isNaN(iso.getTime())) return undefined;
    return iso.toISOString();
  };

  const fetchFlows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const startIso = buildIso(startDate, startTime);
      const endIso = buildIso(endDate, endTime);
      const data = await getFlows({
        skip,
        limit,
        src_ip: srcIp.trim() || undefined,
        dst_ip: dstIp.trim() || undefined,
        protocol: protocol || undefined,
        start_time: startIso,
        end_time: endIso,
      });
      const list = data.flows || data.items || [];
      setFlows(list);
      setTotal(data.total ?? list.length);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load flow summaries');
    } finally {
      setLoading(false);
    }
  }, [skip, limit, srcIp, dstIp, protocol, startDate, startTime, endDate, endTime]);

  useEffect(() => {
    fetchFlows();
  }, [fetchFlows]);

  const handleReset = () => {
    setSrcIp('');
    setDstIp('');
    setProtocol('');
    setStartDate('');
    setStartTime('');
    setEndDate('');
    setEndTime('');
    setSkip(0);
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-800/80 pb-4">
        <h2 className="text-xl font-bold text-slate-100 tracking-tight">Flow Summaries Explorer</h2>
      </div>

      {error && <ErrorMessage message={error} onRetry={fetchFlows} />}

      <FlowFilters
        srcIp={srcIp}
        dstIp={dstIp}
        protocol={protocol}
        startDate={startDate}
        startTime={startTime}
        endDate={endDate}
        endTime={endTime}
        onSrcIpChange={(val) => {
          setSrcIp(val);
          setSkip(0);
        }}
        onDstIpChange={(val) => {
          setDstIp(val);
          setSkip(0);
        }}
        onProtocolChange={(val) => {
          setProtocol(val);
          setSkip(0);
        }}
        onStartDateChange={(val) => {
          setStartDate(val);
          setSkip(0);
        }}
        onStartTimeChange={(val) => {
          setStartTime(val);
          setSkip(0);
        }}
        onEndDateChange={(val) => {
          setEndDate(val);
          setSkip(0);
        }}
        onEndTimeChange={(val) => {
          setEndTime(val);
          setSkip(0);
        }}
        onReset={handleReset}
      />

      <FlowTable flows={flows} loading={loading} />

      <Pagination
        skip={skip}
        limit={limit}
        total={total}
        onPageChange={(newSkip) => setSkip(newSkip)}
      />
    </div>
  );
};
