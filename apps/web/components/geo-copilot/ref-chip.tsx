type RefChipProps = {
  value: string;
  active?: boolean;
  onSelect?: (value: string) => void;
};

export function RefChip({ value, active = false, onSelect }: RefChipProps) {
  return (
    <button
      type="button"
      className={`ref-chip${active ? " active" : ""}`}
      onClick={() => onSelect?.(value)}
      title={value}
      aria-pressed={active}
    >
      {value}
    </button>
  );
}

type RefChipListProps = {
  refs: string[];
  selectedRef: string | null;
  onSelectRef: (value: string) => void;
};

export function RefChipList({ refs, selectedRef, onSelectRef }: RefChipListProps) {
  if (refs.length === 0) {
    return null;
  }
  return (
    <div className="ref-list">
      {refs.map((item) => (
        <RefChip key={item} value={item} active={selectedRef === item} onSelect={onSelectRef} />
      ))}
    </div>
  );
}
