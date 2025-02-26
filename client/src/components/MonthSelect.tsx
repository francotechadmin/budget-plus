import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { months_text } from "@/lib/constants";

interface MonthSelectProps {
  selectedMonth: string;
  onMonthSelect: (value: string) => void;
  dates: string[];
}

export function MonthSelect({
  selectedMonth,
  onMonthSelect,
  dates,
}: MonthSelectProps) {
  if (!dates || dates.length === 0) {
    return <div>No data available. Add Transactions to see data.</div>;
  }

  return (
    <Select onValueChange={onMonthSelect} defaultValue={selectedMonth}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a month" />
      </SelectTrigger>
      <SelectContent>
        {dates.map((dateString: string) => {
          const [yr, mon] = dateString.split("-");
          const monthIndex = parseInt(mon, 10) - 1;
          return (
            <SelectItem key={dateString} value={dateString}>
              {months_text[monthIndex]} {yr}
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}
