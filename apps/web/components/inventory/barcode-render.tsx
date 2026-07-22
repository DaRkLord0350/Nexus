'use client';

import JsBarcode from 'jsbarcode';
import QRCode from 'qrcode';
import { Download } from 'lucide-react';
import { useEffect, useRef } from 'react';
import type { BarcodeFormat } from '@/lib/types';

const JSBARCODE_FORMAT: Record<Exclude<BarcodeFormat, 'qr'>, string> = {
  ean13: 'EAN13',
  upc: 'UPC',
  code128: 'CODE128',
};

interface BarcodeRenderProps {
  value: string;
  format: BarcodeFormat;
  label?: string;
}

export function BarcodeRender({ value, format, label }: BarcodeRenderProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (format === 'qr') {
      QRCode.toCanvas(canvas, value, { width: 160, margin: 1 }).catch(() => {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          canvas.width = 160;
          canvas.height = 40;
          ctx.font = '12px sans-serif';
          ctx.fillText('Invalid QR value', 4, 20);
        }
      });
      return;
    }

    try {
      JsBarcode(canvas, value, { format: JSBARCODE_FORMAT[format], displayValue: true, height: 60, width: 2, fontSize: 14 });
    } catch {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        canvas.width = 220;
        canvas.height = 40;
        ctx.font = '12px sans-serif';
        ctx.fillText(`Invalid value for ${format.toUpperCase()}`, 4, 20);
      }
    }
  }, [value, format]);

  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `${label ?? value}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <canvas ref={canvasRef} className="max-w-full" />
      <button
        type="button"
        onClick={handleDownload}
        className="flex items-center gap-1.5 rounded-lg border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
      >
        <Download size={12} /> Download
      </button>
    </div>
  );
}
