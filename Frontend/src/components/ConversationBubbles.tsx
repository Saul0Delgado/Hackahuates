import React from 'react';
import { motion } from 'framer-motion';
import { Badge } from './ui/badge';
import { Mic, MessageCircle } from 'lucide-react';

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ConversationBubblesProps {
  messages: ConversationMessage[];
  isLoading?: boolean;
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 30
    }
  }
};

export function ConversationBubbles({
  messages,
  isLoading = false
}: ConversationBubblesProps) {
  const typingAnimation = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const dotAnimation = {
    hidden: { opacity: 0.5, y: 0 },
    show: {
      opacity: 1,
      y: [-4, 4, -4],
      transition: {
        duration: 0.8,
        repeat: Infinity
      }
    }
  };

  return (
    <motion.div
      className="space-y-4 flex flex-col"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {messages.length === 0 ? (
        <motion.div
          className="flex flex-col items-center justify-center py-12 text-center"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <MessageCircle className="w-16 h-16 text-slate-300 mb-4" />
          </motion.div>
          <p className="text-slate-400 text-sm">
            Haz una pregunta sobre el drawer para empezar...
          </p>
        </motion.div>
      ) : (
        <>
          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              variants={item}
              className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <motion.div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.role === 'user'
                    ? 'bg-blue-500'
                    : 'bg-gradient-to-br from-purple-500 to-cyan-500'
                }`}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 40 }}
              >
                {msg.role === 'user' ? (
                  <Mic className="w-4 h-4 text-white" />
                ) : (
                  <span className="text-white text-xs font-bold">AI</span>
                )}
              </motion.div>

              {/* Message content */}
              <div className={`flex flex-col gap-1 max-w-xs ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                {/* Badge with role */}
                <Badge
                  variant={msg.role === 'user' ? 'default' : 'secondary'}
                  className="text-xs"
                >
                  {msg.role === 'user' ? 'Tú' : 'Asistente'}
                </Badge>

                {/* Message bubble */}
                <motion.div
                  className={`px-4 py-3 rounded-2xl max-w-xs break-words ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-none'
                      : 'bg-slate-100 text-slate-900 rounded-bl-none'
                  }`}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{
                    type: 'spring',
                    stiffness: 300,
                    damping: 30
                  }}
                  whileHover={{ scale: 1.02 }}
                >
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                </motion.div>

                {/* Timestamp */}
                <motion.p
                  className="text-xs text-slate-400 mt-1"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  {msg.timestamp.toLocaleTimeString('es-ES', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </motion.p>
              </div>
            </motion.div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <motion.div
              variants={item}
              className="flex gap-3"
            >
              <motion.div
                className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-gradient-to-br from-purple-500 to-cyan-500"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
              >
                <span className="text-white text-xs font-bold">AI</span>
              </motion.div>

              <div className="flex flex-col gap-1">
                <Badge variant="secondary" className="text-xs">
                  Asistente
                </Badge>

                <motion.div
                  className="px-4 py-3 rounded-2xl rounded-bl-none bg-slate-100"
                  variants={typingAnimation}
                  initial="hidden"
                  animate="show"
                >
                  <div className="flex gap-1.5">
                    {[...Array(3)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="w-2 h-2 rounded-full bg-slate-400"
                        variants={dotAnimation}
                      />
                    ))}
                  </div>
                </motion.div>
              </div>
            </motion.div>
          )}
        </>
      )}
    </motion.div>
  );
}
