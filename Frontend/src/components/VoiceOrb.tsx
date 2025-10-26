import React from 'react';
import { motion } from 'framer-motion';
import { Mic, Volume2, Loader2 } from 'lucide-react';

export type VoiceOrbState = 'idle' | 'listening' | 'processing' | 'speaking';

interface VoiceOrbProps {
  state: VoiceOrbState;
  onToggle: () => void;
  isDisabled?: boolean;
}

interface StateConfig {
  scale: number;
  backgroundColor: string;
  secondaryColor: string;
  boxShadow: string;
  icon: React.ComponentType<any>;
  animation: 'breathing' | 'pulse' | 'wave' | 'spin';
}

export function VoiceOrb({
  state,
  onToggle,
  isDisabled = false
}: VoiceOrbProps) {
  const getStateConfig = (state: VoiceOrbState): StateConfig => {
    const configs: Record<VoiceOrbState, StateConfig> = {
      idle: {
        scale: 1,
        backgroundColor: '#04016D', // navy_blue default
        boxShadow: '0 0 20px rgba(4, 1, 109, 0.4), 0 0 40px rgba(27, 19, 253, 0.2)',
        secondaryColor: '#1b13fd', // navy_blue 700
        icon: Mic,
        animation: 'breathing'
      },
      listening: {
        scale: 1.05,
        backgroundColor: '#0f0caf', // federal_blue 600
        boxShadow: '0 0 50px rgba(15, 12, 175, 0.6), 0 0 80px rgba(32, 29, 239, 0.3)',
        secondaryColor: '#201def', // federal_blue 700
        icon: Mic,
        animation: 'pulse'
      },
      processing: {
        scale: 1.02,
        backgroundColor: '#0006b8', // navy_blue 600 (the third navy variant)
        boxShadow: '0 0 40px rgba(0, 6, 184, 0.5), 0 0 60px rgba(10, 18, 255, 0.4)',
        secondaryColor: '#0a12ff', // navy_blue 700 (third variant)
        icon: Loader2,
        animation: 'spin'
      },
      speaking: {
        scale: 1.05,
        backgroundColor: '#6b68f5', // federal_blue 800
        boxShadow: '0 0 50px rgba(107, 104, 245, 0.6), 0 0 80px rgba(181, 180, 250, 0.3)',
        secondaryColor: '#d7d7e9', // lavender web default
        icon: Volume2,
        animation: 'wave'
      }
    };
    return configs[state];
  };

  const config = getStateConfig(state);
  const Icon = config.icon;

  // Type-safe animation variants
  const orbVariants: Record<string, any> = {
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
      <div className="relative flex flex-col items-center justify-center gap-8">
        {/* Animated glow background */}
        <motion.div
          className="absolute w-80 h-80 rounded-full"
          style={{
            background: `radial-gradient(circle, ${config.backgroundColor}66 0%, ${config.secondaryColor}33 50%, transparent 70%)`,
            filter: 'blur(40px)'
          }}
          animate={glowVariants[state]}
        />
  
        {/* Main orb button */}
        <motion.button
          onClick={onToggle}
          disabled={isDisabled}
          className="relative z-10 w-32 h-32 rounded-full flex items-center justify-center cursor-pointer transition-all duration-200 disabled:cursor-not-allowed shadow-2xl"
          style={{
            background: `linear-gradient(135deg, ${config.backgroundColor}, ${config.secondaryColor}cc)`,
            boxShadow: config.boxShadow,
            border: '2px solid rgba(215, 215, 233, 0.1)'
          }}
          animate={orbVariants[config.animation] as any}
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
  
          {/* Ripple effect for listening state - MOVED INSIDE BUTTON */}
          {(state === 'listening' || state === 'speaking') && (
            <>
              {[...Array(2)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute rounded-full border pointer-events-none"
                  style={{
                    borderColor: config.secondaryColor,
                    borderWidth: '2px',
                    width: '100%',
                    height: '100%',
                    top: 0,
                    left: 0
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
      </div>
    );
  }