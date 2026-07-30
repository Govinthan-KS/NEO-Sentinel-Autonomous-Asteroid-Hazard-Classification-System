
interface PaginationControlsProps {
  totalRows: number;
  rowsPerPage: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  onRowsPerPageChange: (rows: number) => void;
}

export function PaginationControls({
  totalRows,
  rowsPerPage,
  currentPage,
  onPageChange,
  onRowsPerPageChange
}: PaginationControlsProps) {
  const totalPages = Math.ceil(totalRows / rowsPerPage) || 1;

  // Generate page numbers
  const getPageNumbers = () => {
    const pages = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      if (currentPage <= 4) {
        pages.push(1, 2, 3, 4, 5, '...', totalPages);
      } else if (currentPage >= totalPages - 3) {
        pages.push(1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
      } else {
        pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
      }
    }
    return pages;
  };

  return (
    <div className="flex items-center justify-between mt-5 text-xs font-mono text-[#c7d3ee]">
      <div className="flex items-center gap-4">
        <span>
          Showing {totalRows === 0 ? 0 : (currentPage - 1) * rowsPerPage + 1} to {Math.min(currentPage * rowsPerPage, totalRows)} of {totalRows}
        </span>
        <div className="flex items-center gap-2">
          <span>Rows per page:</span>
          <select 
            value={rowsPerPage} 
            onChange={(e) => onRowsPerPageChange(Number(e.target.value))}
            className="bg-[rgba(150,190,255,0.05)] border border-[rgba(150,190,255,0.2)] rounded px-1 py-0.5 outline-none focus:border-primary-bright"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      <div className="flex items-center gap-1.5">
        <button 
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="px-2.5 py-1.5 rounded bg-[rgba(150,190,255,0.05)] border border-[rgba(150,190,255,0.1)] hover:bg-[rgba(150,190,255,0.15)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Prev
        </button>

        {getPageNumbers().map((p, idx) => (
          <button
            key={idx}
            onClick={() => typeof p === 'number' && onPageChange(p)}
            disabled={p === '...'}
            className={`min-w-[28px] px-2 py-1.5 rounded border transition-colors ${
              p === currentPage 
                ? 'bg-primary/20 border-primary text-[#eef3ff]' 
                : p === '...'
                ? 'bg-transparent border-transparent text-[#5c6f94] cursor-default'
                : 'bg-[rgba(150,190,255,0.05)] border-[rgba(150,190,255,0.1)] hover:bg-[rgba(150,190,255,0.15)] text-[#c7d3ee]'
            }`}
          >
            {p}
          </button>
        ))}

        <button 
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          className="px-2.5 py-1.5 rounded bg-[rgba(150,190,255,0.05)] border border-[rgba(150,190,255,0.1)] hover:bg-[rgba(150,190,255,0.15)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
}
