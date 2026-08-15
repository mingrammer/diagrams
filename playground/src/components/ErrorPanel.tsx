interface Props {
  error: string | null;
  testId?: string;
}

export default function ErrorPanel({ error, testId = "error-panel" }: Props) {
  if (!error) return null;
  return (
    <pre className="error-panel" data-testid={testId}>
      {error}
    </pre>
  );
}
