import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface AudioWaveVisualizerProps {
  isListening: boolean;
  variant?: 'bars' | 'circular' | 'ripple';
  color?: string;
}

export function AudioWaveVisualizer({
  isListening,
  variant = 'bars',
  color = 'rgb(99, 102, 241)' // indigo-500
}: AudioWaveVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const animationIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isListening) {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      return;
    }

    const initAudio = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        if (!audioContextRef.current) {
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
          audioContextRef.current = audioContext;

          const analyser = audioContext.createAnalyser();
          analyser.fftSize = 256;
          analyserRef.current = analyser;

          const dataArray = new Uint8Array(analyser.frequencyBinCount);
          dataArrayRef.current = dataArray;

          const source = audioContext.createMediaStreamSource(stream);
          source.connect(analyser);
        }

        draw();
      } catch (err) {
        console.error('Audio access error:', err);
      }
    };

    const draw = () => {
      const canvas = canvasRef.current;
      const analyser = analyserRef.current;
      const dataArray = dataArrayRef.current;

      if (!canvas || !analyser || !dataArray) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      analyser.getByteFrequencyData(dataArray);

      // Clear canvas
      ctx.fillStyle = 'rgba(255, 255, 255, 0)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      if (variant === 'bars') {
        drawBars(ctx, dataArray, canvas);
      } else if (variant === 'circular') {
        drawCircular(ctx, dataArray, canvas);
      } else if (variant === 'ripple') {
        drawRipple(ctx, dataArray, canvas);
      }

      animationIdRef.current = requestAnimationFrame(draw);
    };

    initAudio();

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
    };
  }, [isListening, variant]);

  const drawBars = (
    ctx: CanvasRenderingContext2D,
    dataArray: Uint8Array,
    canvas: HTMLCanvasElement
  ) => {
    const barWidth = (canvas.width / dataArray.length) * 2.5;
    let x = 0;

    for (let i = 0; i < dataArray.length; i++) {
      const barHeight = (dataArray[i] / 255) * canvas.height;

      // Gradient
      const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, color);
      gradient.addColorStop(1, `${color}44`);
      ctx.fillStyle = gradient;

      ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
      x += barWidth + 1;
    }
  };

  const drawCircular = (
    ctx: CanvasRenderingContext2D,
    dataArray: Uint8Array,
    canvas: HTMLCanvasElement
  ) => {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 50;

    // Draw circular wave
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;

    for (let i = 0; i < dataArray.length; i++) {
      const angle = (i / dataArray.length) * Math.PI * 2;
      const distance = (dataArray[i] / 255) * 30 + radius;

      const x = centerX + Math.cos(angle) * distance;
      const y = centerY + Math.sin(angle) * distance;

      if (i === 0) {
        ctx.beginPath();
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }

    ctx.closePath();
    ctx.stroke();

    // Draw center circle
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(centerX, centerY, 8, 0, Math.PI * 2);
    ctx.fill();
  };

  const drawRipple = (
    ctx: CanvasRenderingContext2D,
    dataArray: Uint8Array,
    canvas: HTMLCanvasElement
  ) => {
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const baseRadius = 40;

    // Average frequency for ripple effect
    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
    const rippleAmount = (average / 255) * 20;

    // Draw multiple ripples
    for (let ripple = 0; ripple < 3; ripple++) {
      const currentRadius = baseRadius + ripple * 15 + rippleAmount;
      const alpha = 1 - (ripple * 0.3 + rippleAmount / 20);

      ctx.strokeStyle = color.replace('rgb', 'rgba').replace(')', `, ${alpha})`);
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(centerX, centerY, currentRadius, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Center circle glow
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.8;
    ctx.beginPath();
    ctx.arc(centerX, centerY, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  };

  return (
    <canvas
      ref={canvasRef}
      width={300}
      height={200}
      className="w-full h-48 rounded-lg"
    />
  );
}
