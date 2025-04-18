import React, { useState, useEffect, useRef, useMemo } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, GridApi } from 'ag-grid-community';
import { Empty } from 'antd';
import LoadingButton from './loading';



interface AutoSizingAgGridProps {
  columnDefs: ColDef[];
  rowData: any[];
  maxRows?: number;
  rowHeight?: number;
  headerHeight?: number;
  className?: string;
}

const AutoSizingAgGrid: React.FC<AutoSizingAgGridProps> = ({
  columnDefs,
  rowData,
  maxRows = 15,
  rowHeight = 30,
  headerHeight = 50,
  className = '',
}) => {
  const gridRef = useRef<AgGridReact>(null);
  const [gridApi, setGridApi] = useState<GridApi | null>(null);
  const [gridHeight, setGridHeight] = useState<string>('auto');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Memoize default column definitions to prevent unnecessary re-renders
  const defaultColDef = useMemo(() => ({
    filter: true,
    floatingFilter: true,
    wrapHeaderText: true,
    flex: 1,
    autoHeaderHeight: true,
    autoHeight: true,
    sortable: true,
    wrapText: true,
    cellStyle: { 
      whiteSpace: "normal", 
      lineHeight: "20px" 
    }
  }), []);

  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api);
  };

  // Manage loading state
  useEffect(() => {
    if (rowData.length > 0) {
      const loadingTimeout = setTimeout(() => {
        setIsLoading(false);
      }, 500);

      return () => clearTimeout(loadingTimeout);
    } else {
      setIsLoading(false);
    }
  }, [rowData]);

  // Calculate and set grid height
  useEffect(() => {
    if (gridApi) {
      const rowCount = rowData.length;
      const calculatedHeight = (rowCount * rowHeight) + headerHeight;
      const maxHeight = (maxRows * rowHeight) + headerHeight;

      // Add some padding to ensure all content is visible
      const finalHeight = rowCount <= maxRows 
        ? `${calculatedHeight + 50}px`
        : `${maxHeight}px`;

      setGridHeight(finalHeight);

      // Ensure grid layout is responsive
      gridApi.setGridOption('domLayout', 'normal');
    }
  }, [rowData, gridApi, maxRows, rowHeight, headerHeight]);

  // Render loading state
  if (isLoading) {
    return <LoadingButton />;
  }

  // Render empty state
  if (rowData.length === 0) {
    return (
      <div className="h-[40vh] flex items-center justify-center">
        <Empty description="No data available" />
      </div>
    );
  }

  return (
    <div 
      className={`ag-theme-quartz ${className}`} 
      style={{ 
        height: gridHeight, 
        width: '100%' 
      }}
    >
      <AgGridReact
        ref={gridRef}
        columnDefs={columnDefs}
        rowData={rowData}
        defaultColDef={defaultColDef}
        onGridReady={onGridReady}
        rowHeight={rowHeight}
        pagination={true}
        paginationPageSize={20}
        // Removed commented-out headerHeight
        domLayout="normal"
        suppressColumnVirtualisation={true}
        suppressRowVirtualisation={true}
        enableRangeSelection={true}
        enableCellTextSelection={true}
      />
    </div>
  );
};

export default React.memo(AutoSizingAgGrid);