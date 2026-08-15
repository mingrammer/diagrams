import { EXAMPLES } from "../examples";

interface Props {
  activeExample: string | null;
  onSelect: (example: { title: string; code: string }) => void;
}

export default function ExamplesGallery({ activeExample, onSelect }: Props) {
  return (
    <div className="examples">
      <span className="examples-label">Examples</span>
      {EXAMPLES.map((example) => (
        <button
          key={example.title}
          className={`example-pill${example.title === activeExample ? " is-active" : ""}`}
          onClick={() => onSelect(example)}
        >
          {example.title}
        </button>
      ))}
    </div>
  );
}
