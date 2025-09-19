type LoadingStateProps = {
  message?: string;
};

export default function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '2rem',
      fontSize: '1.1rem',
      color: '#666'
    }}>
      {message}
    </div>
  );
}
