import React, { useState } from "react";
import { Dropdown, Button, Checkbox, Menu } from "antd";
import { SlidersHorizontalIcon } from "lucide-react";
interface ColumnFilterProps {
  allColumns: Record<string, any>[]; // Accepts any structure for column objects
  onChange: (selectedColumns: string[]) => void;
  defaultSelectedColumns: string[];
}

const ColumnFilter: React.FC<ColumnFilterProps> = ({
  allColumns,
  onChange,
  defaultSelectedColumns,
}) => {
  const [selectedColumns, setSelectedColumns] = useState(defaultSelectedColumns);
  const [dropdownVisible, setDropdownVisible] = useState(false);

  const handleCheckboxChange = (field: string, checked: boolean) => {
    const updatedSelection = checked
      ? [...selectedColumns, field]
      : selectedColumns.filter((col) => col !== field);
    setSelectedColumns(updatedSelection);
    onChange(updatedSelection);
  };

  const menu = (
    <Menu>
      {allColumns.map((col) => (
        <Menu.Item key={col.field}>
          <Checkbox
            checked={selectedColumns.includes(col.field)}
            onChange={(e) => handleCheckboxChange(col.field, e.target.checked)}
          >
            {col.headerName || col.field}
          </Checkbox>
        </Menu.Item>
      ))}
    </Menu>
  );

  return (
    <div className="column-filter">
      <Dropdown
        overlay={menu}
        open={dropdownVisible}
        onOpenChange={(visible) => setDropdownVisible(visible)}
        trigger={['click']}
      >
        <Button type="primary" className="p-2 text-center "><SlidersHorizontalIcon className="h-5 mr w-7" /> Column selector </Button>
      </Dropdown>
    </div>
  );
};

export default ColumnFilter;
