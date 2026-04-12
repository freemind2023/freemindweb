/* ============================================================
   FREE MIND CONSULTANCY — particles.js
   Neural network canvas animation for hero background
   80 nodes, connected within 120px, 60fps via requestAnimationFrame
   ============================================================ */

(function () {
  'use strict';

  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const NODE_COUNT = 80;
  const CONNECTION_DISTANCE = 120;
  const NODE_RADIUS = 2;
  const SPEED = 0.4;

  let nodes = [];
  let animFrame;
  let isDark = false;

  function getColors() {
    isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      node: isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.20)',
      line: isDark ? 'rgba(255,255,255,' : 'rgba(0,0,0,'
    };
  }

  function resize() {
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }

  function createNode() {
    return {
      x:  Math.random() * canvas.width,
      y:  Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * SPEED,
      vy: (Math.random() - 0.5) * SPEED
    };
  }

  function init() {
    resize();
    nodes = Array.from({ length: NODE_COUNT }, createNode);
  }

  function update() {
    nodes.forEach(n => {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > canvas.width)  n.vx *= -1;
      if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
    });
  }

  function draw() {
    const { node: nodeColor, line: linePrefix } = getColors();
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw connections
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < CONNECTION_DISTANCE) {
          const opacity = (1 - dist / CONNECTION_DISTANCE) * 0.6;
          ctx.beginPath();
          ctx.strokeStyle = linePrefix + opacity.toFixed(3) + ')';
          ctx.lineWidth = 0.8;
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw nodes
    ctx.fillStyle = nodeColor;
    nodes.forEach(n => {
      ctx.beginPath();
      ctx.arc(n.x, n.y, NODE_RADIUS, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function loop() {
    update();
    draw();
    animFrame = requestAnimationFrame(loop);
  }

  // Handle window resize
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      resize();
      nodes.forEach(n => {
        n.x = Math.min(n.x, canvas.width);
        n.y = Math.min(n.y, canvas.height);
      });
    }, 150);
  });

  // Pause when tab is hidden (performance)
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(animFrame);
    } else {
      loop();
    }
  });

  // Initialize
  init();
  loop();
})();
