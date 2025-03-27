// Create a simple logo for DocuInsight AI using SVG
const canvas = document.createElement('canvas');
canvas.width = 500;
canvas.height = 500;
const ctx = canvas.getContext('2d');

// Background
ctx.fillStyle = '#4361ee';
ctx.beginPath();
ctx.arc(250, 250, 240, 0, Math.PI * 2);
ctx.fill();

// Document shape
ctx.fillStyle = '#ffffff';
ctx.fillRect(150, 120, 200, 260);

// Document fold
ctx.fillStyle = '#e6e6e6';
ctx.beginPath();
ctx.moveTo(350, 120);
ctx.lineTo(350, 170);
ctx.lineTo(300, 120);
ctx.closePath();
ctx.fill();

// Magnifying glass
ctx.strokeStyle = '#ffffff';
ctx.lineWidth = 20;
ctx.beginPath();
ctx.arc(300, 300, 70, 0, Math.PI * 2);
ctx.stroke();

// Magnifying glass handle
ctx.beginPath();
ctx.moveTo(240, 360);
ctx.lineTo(180, 420);
ctx.stroke();

// AI text
ctx.fillStyle = '#ffffff';
ctx.font = 'bold 60px Arial';
ctx.fillText('AI', 220, 310);

// Export to PNG
const dataUrl = canvas.toDataURL('image/png');
console.log(dataUrl);
