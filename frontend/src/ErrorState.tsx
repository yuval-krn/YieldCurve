type ErrorStateProps = {
  error: string;
  onRetry?: () => void;
};

export default function ErrorState({ error, onRetry }: ErrorStateProps) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '2rem',
      color: '#d32f2f',
      backgroundColor: '#ffebee',
      border: '1px solid #ffcdd2',
      borderRadius: '4px',
      margin: '1rem 0'
    }}>
      <h3 style={{ margin: '0 0 1rem 0', color: '#d32f2f' }}>Error</h3>
      <p style={{ margin: '0 0 1rem 0', textAlign: 'center' }}>{error}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#d32f2f',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Try Again
        </button>
      )}
    </div>
  );
}
