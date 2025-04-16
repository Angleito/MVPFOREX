export default function ModelButton({ model, onClick, loading }) {
  return (
    <button
      onClick={onClick}
      style={{
        margin: '0 12px 12px 0',
        padding: '12px 20px',
        fontSize: 16,
        background: '#ffd700',
        border: '1px solid #c9b037',
        borderRadius: 8,
        cursor: loading ? 'wait' : 'pointer',
        opacity: loading ? 0.6 : 1,
        fontWeight: 'bold',
      }}
      disabled={loading}
    >
      Analyze with {model}
    </button>
  );
}
