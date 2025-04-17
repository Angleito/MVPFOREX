import React from 'react';
import Error from 'next/error';

function CustomError({ statusCode }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      padding: '20px',
      textAlign: 'center',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1 style={{ fontSize: '24px', marginBottom: '16px' }}>
        {statusCode
          ? `An error ${statusCode} occurred on server`
          : 'An error occurred on client'}
      </h1>
      <p style={{ fontSize: '16px', color: '#666' }}>
        Please try refreshing the page or contact support if the problem persists.
      </p>
      <button
        onClick={() => window.location.reload()}
        style={{
          marginTop: '20px',
          padding: '10px 16px',
          background: '#0070f3',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '14px'
        }}
      >
        Refresh Page
      </button>
    </div>
  );
}

CustomError.getInitialProps = ({ res, err }) => {
  // When Error is imported from 'next/error' this ensures pages with
  // getInitialProps work properly with error handling
  const statusCode = res ? res.statusCode : err ? err.statusCode : 404;
  return { statusCode };
};

export default CustomError;
