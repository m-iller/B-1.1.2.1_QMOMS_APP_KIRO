interface ErrorBannerProps {
  error: Error | null
}

export function ErrorBanner({ error }: ErrorBannerProps) {
  if (!error) return null
  return (
    <div style={{ background: '#fee2e2', color: '#991b1b', padding: '8px 16px', borderRadius: 4, marginBottom: 8 }}>
      ⚠ {error.message}
    </div>
  )
}
