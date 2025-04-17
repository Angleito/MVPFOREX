import React from 'react';
import Head from 'next/head';
import Link from 'next/link';

export default function Custom404() {
  return (
    <>
      <Head>
        <title>404 - Page Not Found | XAUUSD Trading Dashboard</title>
      </Head>
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
        <h1 style={{ fontSize: '32px', marginBottom: '16px' }}>404 - Page Not Found</h1>
        <p style={{ fontSize: '16px', color: '#666', maxWidth: '500px', margin: '0 auto 24px' }}>
          The page you are looking for does not exist or has been moved.
        </p>
        <Link href="/" passHref>
          <button style={{
            padding: '10px 16px',
            background: '#0070f3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}>
            Return to Dashboard
          </button>
        </Link>
      </div>
    </>
  );
}
