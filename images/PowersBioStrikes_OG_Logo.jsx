import { useRef, useEffect, useState } from 'react';

export default function OGImageGenerator() {
  const canvasRef = useRef(null);
  const [downloadUrl, setDownloadUrl] = useState(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Background gradient
    const bgGrad = ctx.createLinearGradient(0, 0, 1200, 630);
    bgGrad.addColorStop(0, '#F8FAFC');
    bgGrad.addColorStop(1, '#E2E8F0');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, 1200, 630);

    // Subtle grid pattern
    ctx.strokeStyle = 'rgba(0, 102, 204, 0.03)';
    ctx.lineWidth = 1;
    for (let x = 0; x < 1200; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, 630);
      ctx.stroke();
    }
    for (let y = 0; y < 630; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(1200, y);
      ctx.stroke();
    }

    const centerX = 600;
    const centerY = 315;
    const boltX = centerX - 320;
    const boltY = centerY - 100;
    const scale = 2.2;

    // Bolt gradient
    const boltGrad = ctx.createLinearGradient(boltX, boltY, boltX + 60 * scale, boltY + 95 * scale);
    boltGrad.addColorStop(0, '#00D4FF');
    boltGrad.addColorStop(1, '#0066CC');

    // Draw lightning bolt
    ctx.fillStyle = boltGrad;
    ctx.beginPath();
    ctx.moveTo(boltX + 45 * scale, boltY + 5 * scale);
    ctx.lineTo(boltX + 25 * scale, boltY + 45 * scale);
    ctx.lineTo(boltX + 38 * scale, boltY + 45 * scale);
    ctx.lineTo(boltX + 20 * scale, boltY + 95 * scale);
    ctx.lineTo(boltX + 55 * scale, boltY + 40 * scale);
    ctx.lineTo(boltX + 40 * scale, boltY + 40 * scale);
    ctx.closePath();
    ctx.fill();

    // Molecule nodes
    ctx.globalAlpha = 0.9;
    ctx.fillStyle = '#00D4FF';
    ctx.beginPath();
    ctx.arc(boltX + 20 * scale, boltY + 95 * scale, 6 * scale, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#0066CC';
    ctx.beginPath();
    ctx.arc(boltX + 45 * scale, boltY + 5 * scale, 5 * scale, 0, Math.PI * 2);
    ctx.fill();

    ctx.globalAlpha = 0.7;
    ctx.fillStyle = '#00D4FF';
    ctx.beginPath();
    ctx.arc(boltX + 55 * scale, boltY + 40 * scale, 4 * scale, 0, Math.PI * 2);
    ctx.fill();

    // Connecting lines
    ctx.globalAlpha = 0.5;
    ctx.strokeStyle = '#00D4FF';
    ctx.lineWidth = 1.5 * scale;
    ctx.beginPath();
    ctx.moveTo(boltX + 20 * scale, boltY + 89 * scale);
    ctx.lineTo(boltX + 25 * scale, boltY + 75 * scale);
    ctx.stroke();

    ctx.strokeStyle = '#0066CC';
    ctx.beginPath();
    ctx.moveTo(boltX + 55 * scale, boltY + 36 * scale);
    ctx.lineTo(boltX + 60 * scale, boltY + 25 * scale);
    ctx.stroke();

    ctx.globalAlpha = 1;

    const textX = centerX - 80;
    const textY = centerY - 10;

    // Main text
    ctx.font = 'bold 72px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    const textGrad = ctx.createLinearGradient(textX, textY - 50, textX + 400, textY);
    textGrad.addColorStop(0, '#0A1628');
    textGrad.addColorStop(1, '#1A365D');
    ctx.fillStyle = textGrad;
    ctx.fillText('Powers', textX, textY);

    const powersWidth = ctx.measureText('Powers').width;

    ctx.fillStyle = '#0066CC';
    ctx.fillText('Bio', textX + powersWidth, textY);

    const bioWidth = ctx.measureText('Bio').width;

    const strikesGrad = ctx.createLinearGradient(
      textX + powersWidth + bioWidth,
      textY - 50,
      textX + powersWidth + bioWidth + 200,
      textY
    );
    strikesGrad.addColorStop(0, '#00D4FF');
    strikesGrad.addColorStop(1, '#0066CC');
    ctx.fillStyle = strikesGrad;
    ctx.fillText('Strikes', textX + powersWidth + bioWidth, textY);

    // Tagline
    ctx.font = '22px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.fillStyle = '#5A6B7D';
    ctx.fillText('CATALYST OPTIONS TRADING', textX, textY + 50);

    // Generate download URL
    setDownloadUrl(canvas.toDataURL('image/png'));
  }, []);

  const handleDownload = () => {
    const link = document.createElement('a');
    link.download = 'PowersBioStrikes_OG_1200x630.png';
    link.href = downloadUrl;
    link.click();
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      padding: '24px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <div style={{ maxWidth: '1248px', margin: '0 auto' }}>
        <h1 style={{ color: 'white', fontSize: '24px', marginBottom: '8px', fontWeight: 600 }}>
          PowersBioStrikes OG Image
        </h1>
        <p style={{ color: '#94a3b8', marginBottom: '24px' }}>
          1200 × 630 pixels — PNG format for social sharing (X, Facebook, LinkedIn)
        </p>

        <div style={{
          background: '#1e293b',
          borderRadius: '12px',
          padding: '24px',
          marginBottom: '24px'
        }}>
          <canvas
            ref={canvasRef}
            width={1200}
            height={630}
            style={{
              width: '100%',
              height: 'auto',
              borderRadius: '8px',
              border: '1px solid #334155'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button
            onClick={handleDownload}
            disabled={!downloadUrl}
            style={{
              background: 'linear-gradient(135deg, #00D4FF 0%, #0066CC 100%)',
              color: 'white',
              border: 'none',
              padding: '14px 28px',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Download PNG
          </button>
        </div>

        <div style={{
          marginTop: '24px',
          padding: '16px',
          background: '#1e293b',
          borderRadius: '8px',
          borderLeft: '3px solid #00D4FF'
        }}>
          <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>
            <strong style={{ color: '#00D4FF' }}>Usage:</strong> Upload this PNG as your Open Graph image for social media link previews. 
            Most platforms like X, Facebook, and LinkedIn will display this when your link is shared.
          </p>
        </div>
      </div>
    </div>
  );
}
