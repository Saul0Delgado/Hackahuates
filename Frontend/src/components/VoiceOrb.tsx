import React from 'react';
import { motion } from 'framer-motion';
import { Mic, Square, Volume2, Loader2 } from 'lucide-react';

export type VoiceOrbState = 'idle' | 'listening' | 'processing' | 'speaking';

interface VoiceOrbProps {
  state: VoiceOrbState;
  onToggle: () => void;
  isDisabled?: boolean;
}

export function VoiceOrb({
  state,
  onToggle,
  isDisabled = false
}: VoiceOrbProps) {
  const getStateConfig = (state: VoiceOrbState) => {
    const configs = {
      idle: {
        scale: 1,
        backgroundColor: 'rgb(99, 102, 241)',
        boxShadow: '0 0 20px rgba(99, 102, 241, 0.3)',
        icon: Mic,
        animation: 'breathing'
      },
      listening: {
        scale: 1.05,
        backgroundColor: 'rgb(168, 85, 247)',
        boxShadow: '0 0 40px rgba(168, 85, 247, 0.6)',
        icon: Mic,
        animation: 'pulse'
      },
      processing: {
        scale: 1.02,
        backgroundColor: 'rgb(59, 130, 246)',
        boxShadow: '0 0 30px rgba(59, 130, 246, 0.5)',
        icon: Loader2,
        animation: 'spin'
      },
      speaking: {
        scale: 1.05,
        backgroundColor: 'rgb(34, 197, 94)',
        boxShadow: '0 0 40px rgba(34, 197, 94, 0.6)',
        icon: Volume2,
        animation: 'wave'
      }
    };
    return configs[state];
  };

  const config = getStateConfig(state);
  const Icon = config.icon;

  // Animation variants
  const orbVariants = {
    breathing: {
      scale: [1, 1.05, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut'
      }
    },
    pulse: {
      scale: [1.05, 1.15, 1.05],
      transition: {
        duration: 0.6,
        repeat: Infinity,
        ease: 'easeInOut'
      }
    },
    wave: {
      scale: [1.05, 1.1, 1.05],
      transition: {
        duration: 0.8,
        repeat: Infinity,
        ease: 'easeInOut'
      }
    },
    spin: {
      rotate: 360,
      transition: {
        duration: 2,
        repeat: Infinity,
        linear: true
      }
    }
  };

  const glowVariants = {
    idle: {
      opacity: [0.3, 0.5, 0.3],
      scale: [1, 1.1, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut'
      }
    },
    listening: {
      opacity: [0.6, 0.8, 0.6],
      scale: [1.2, 1.5, 1.2],
      transition: {
        duration: 0.6,
        repeat: Infinity,
        ease: 'easeInOut'
      }
    },
    processing: {
      opacity: [0.4, 0.6, 0.4],
      scale: [1.1, 1.3, 1.1],
      transition: {
        duration: 0.8,
        repeat: Infinity,
        ease: 'easeInOut'
      }
    },
    speaking: {
      opacity: [0.5, 0.8, 0.5],
      scale: [1.2, 1.5, 1.2],
      transition: {
        duration: 0.8,
        repeat: Infinity,
        ease: 'easeInOut'
      }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center gap-8">
      {/* Animated glow background */}
      <motion.div
        className="absolute w-80 h-80 rounded-full"
        style={{
          background: `radial-gradient(circle, ${config.backgroundColor}44 0%, transparent 70%)`,
          filter: 'blur(40px)'
        }}
        animate={glowVariants[state]}
      />

      {/* Main orb button */}
      <motion.button
        onClick={onToggle}
        disabled={isDisabled}
        className="relative z-10 w-32 h-32 rounded-full flex items-center justify-center cursor-pointer transition-all duration-200 disabled:cursor-not-allowed"
        style={{
          background: `linear-gradient(135deg, ${config.backgroundColor}, ${config.backgroundColor}dd)`,
          boxShadow: config.boxShadow
        }}
        animate={orbVariants[config.animation]}
        whileHover={isDisabled ? {} : { scale: 1.1 }}
        whileTap={isDisabled ? {} : { scale: 0.95 }}
      >
        {/* Icon animation */}
        <motion.div
          animate={state === 'processing' ? { rotate: 360 } : {}}
          transition={state === 'processing' ? { duration: 1, repeat: Infinity, linear: true } : {}}
        >
          <Icon
            size={48}
            className="text-white drop-shadow-lg"
            strokeWidth={2.5}
          />
        </motion.div>
      </motion.button>

      {/* State label */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <p className="text-sm font-medium text-slate-600">
          {state === 'idle' && 'Pulsa para hablar'}
          {state === 'listening' && 'Escuchando...'}
          {state === 'processing' && 'Procesando...'}
          {state === 'speaking' && 'Respondiendo...'}
        </p>
      </motion.div>

      {/* Ripple effect for listening state */}
      {(state === 'listening' || state === 'speaking') && (
        <>
          {[...Array(2)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute rounded-full"
              style={{
                borderColor: config.backgroundColor,
                width: '128px',
                height: '128px'
              }}
              initial={{ scale: 1, opacity: 0.6 }}
              animate={{
                scale: [1, 1.5],
                opacity: [0.8, 0]
              }}
              transition={{
                duration: 1.5,
                delay: i * 0.4,
                repeat: Infinity,
                ease: 'easeOut'
              }}
            />
          ))}
        </>
      )}
    </div>
  );
}
