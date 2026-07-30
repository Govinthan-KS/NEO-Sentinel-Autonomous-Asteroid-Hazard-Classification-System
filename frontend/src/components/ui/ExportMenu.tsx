import React, { useState, useRef, useEffect } from 'react';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { Download } from 'lucide-react';

interface ExportMenuProps {
  data: any[];
  filename: string;
  columns: { header: string; key: string }[];
  title: string;
}

export function ExportMenu({ data, filename, columns, title }: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on click outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadBlob(blob, `${filename}.json`);
    setIsOpen(false);
  };

  const handleExportCSV = () => {
    if (data.length === 0) return;
    const headers = columns.map(c => c.header).join(',');
    const rows = data.map(row => columns.map(c => JSON.stringify(row[c.key] ?? '')).join(','));
    const csvContent = [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    downloadBlob(blob, `${filename}.csv`);
    setIsOpen(false);
  };

  const handleExportXLSX = () => {
    const worksheetData = [
      columns.map(c => c.header),
      ...data.map(row => columns.map(c => row[c.key]))
    ];
    const ws = XLSX.utils.aoa_to_sheet(worksheetData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Export");
    XLSX.writeFile(wb, `${filename}.xlsx`);
    setIsOpen(false);
  };

  const handleExportPDF = () => {
    const doc = new jsPDF('landscape');
    
    // Add Brand Header
    doc.setFillColor(8, 12, 22); // Dark background
    doc.rect(0, 0, doc.internal.pageSize.width, 30, 'F');
    
    doc.setTextColor(90, 200, 250); // Sky Blue #5ac8fa
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text("NEO-Sentinel — Telemetry & Model Evaluation Report", 14, 20);

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(title, doc.internal.pageSize.width - 14, 20, { align: 'right' });

    // Table
    const tableBody = data.map(row => columns.map(c => String(row[c.key] ?? '')));
    const tableHeaders = [columns.map(c => c.header)];

    autoTable(doc, {
      startY: 35,
      head: tableHeaders,
      body: tableBody,
      theme: 'grid',
      headStyles: { fillColor: [90, 200, 250], textColor: [0, 0, 0], fontStyle: 'bold' },
      styles: { fontSize: 8, cellPadding: 3, textColor: [40, 40, 40] },
      alternateRowStyles: { fillColor: [245, 245, 245] },
    });

    doc.save(`${filename}.pdf`);
    setIsOpen(false);
  };

  const downloadBlob = (blob: Blob, name: string) => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="relative" ref={menuRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 bg-[rgba(150,190,255,0.05)] border border-[rgba(150,190,255,0.2)] hover:bg-[rgba(150,190,255,0.1)] hover:border-primary px-3 py-1.5 rounded-lg text-sm text-[#eef3ff] font-mono transition-colors"
      >
        <Download size={14} /> Export
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-40 bg-[rgba(12,16,28,0.95)] backdrop-blur-lg border border-[rgba(150,190,255,0.2)] rounded-lg shadow-xl z-50 overflow-hidden flex flex-col font-mono text-sm">
          <button onClick={handleExportCSV} className="text-left px-4 py-2 text-[#c7d3ee] hover:bg-[rgba(150,190,255,0.1)] hover:text-[#eef3ff] transition-colors border-b border-[rgba(150,190,255,0.1)]">
            Download .CSV
          </button>
          <button onClick={handleExportJSON} className="text-left px-4 py-2 text-[#c7d3ee] hover:bg-[rgba(150,190,255,0.1)] hover:text-[#eef3ff] transition-colors border-b border-[rgba(150,190,255,0.1)]">
            Download .JSON
          </button>
          <button onClick={handleExportXLSX} className="text-left px-4 py-2 text-[#c7d3ee] hover:bg-[rgba(150,190,255,0.1)] hover:text-[#eef3ff] transition-colors border-b border-[rgba(150,190,255,0.1)]">
            Download .XLSX
          </button>
          <button onClick={handleExportPDF} className="text-left px-4 py-2 text-primary-bright hover:bg-primary/20 transition-colors font-bold">
            Download .PDF
          </button>
        </div>
      )}
    </div>
  );
}
