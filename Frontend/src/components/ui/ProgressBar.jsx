import { C } from '../../constants/theme';

export default function ProgressBar({ value, max = 100, color = C.accent, height = 4 }) {
  return (
    <div style={{ width: '100%', height, background: C.border, borderRadius: height / 2, overflow: 'hidden' }}>
      <div
        style={{
          width: `${(value / max) * 100}%`,
          height: '100%',
          background: color,
          borderRadius: height / 2,
          transition: 'width 0.6s ease',
        }}
      />
    </div>
  );
}
