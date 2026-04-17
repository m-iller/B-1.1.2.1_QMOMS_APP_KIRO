interface Props { count: number }
export function NavBadge({ count }: Props) {
  if (count === 0) return null
  return (
    <span style={{ background: '#dc2626', color: '#fff', borderRadius: '50%', padding: '1px 6px', fontSize: 11, fontWeight: 700, marginLeft: 6 }}>
      {count > 99 ? '99+' : count}
    </span>
  )
}
