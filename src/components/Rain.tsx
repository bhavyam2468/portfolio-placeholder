import { useEffect, useRef } from "react";

interface Raindrop {
  x: number;
  y: number;
  length: number;
  speed: number;
  opacity: number;
  width: number;
}

export default function Rain() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;

    const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
    let width = 0;
    let height = 0;
    let drops: Raindrop[] = [];
    let frame = 0;
    let lastTime = 0;

    const makeDrop = (randomY = true): Raindrop => {
      const depth = Math.random();
      return {
        x: Math.random() * (width + 120),
        y: randomY ? Math.random() * height : -40,
        length: 9 + depth * 22,
        speed: 230 + depth * 250,
        opacity: 0.07 + depth * 0.17,
        width: 0.45 + depth * 0.6,
      };
    };

    const resize = () => {
      const bounds = canvas.getBoundingClientRect();
      const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);
      width = bounds.width;
      height = bounds.height;
      canvas.width = Math.round(width * pixelRatio);
      canvas.height = Math.round(height * pixelRatio);
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      drops = Array.from(
        { length: Math.min(105, Math.max(35, Math.round(width / 15))) },
        () => makeDrop(),
      );
    };

    const draw = (time: number) => {
      // Elapsed time keeps the drizzle gentle on high-refresh-rate displays, too.
      const elapsed = lastTime ? Math.min((time - lastTime) / 1000, 0.04) : 0;
      lastTime = time;
      context.clearRect(0, 0, width, height);

      for (let index = 0; index < drops.length; index += 1) {
        const drop = drops[index];
        drop.y += drop.speed * elapsed;
        drop.x -= drop.speed * elapsed * 0.13;

        if (drop.y > height + 35 || drop.x < -40) {
          drops[index] = makeDrop(false);
          continue;
        }

        context.beginPath();
        context.moveTo(drop.x, drop.y);
        context.lineTo(drop.x - drop.length * 0.13, drop.y + drop.length);
        context.strokeStyle = `rgba(225, 235, 220, ${drop.opacity})`;
        context.lineWidth = drop.width;
        context.stroke();
      }

      frame = window.requestAnimationFrame(draw);
    };

    const syncPlayback = () => {
      window.cancelAnimationFrame(frame);
      lastTime = 0;
      if (!motionPreference.matches && !document.hidden) {
        frame = window.requestAnimationFrame(draw);
      } else {
        context.clearRect(0, 0, width, height);
      }
    };

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    resize();
    syncPlayback();
    motionPreference.addEventListener("change", syncPlayback);
    document.addEventListener("visibilitychange", syncPlayback);

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      motionPreference.removeEventListener("change", syncPlayback);
      document.removeEventListener("visibilitychange", syncPlayback);
    };
  }, []);

  return <canvas ref={canvasRef} className="scene__rain" aria-hidden="true" />;
}