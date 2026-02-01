"use client";

import React, { useState, useEffect } from 'react';

interface NotificationProps {
  message: string;
  type: 'success' | 'info' | 'warning' | 'error';
  duration?: number; // Duration in ms before auto-closing
  onClose: () => void;
}

const notificationStyles = {
  success: {
    bg: 'bg-green-100',
    border: 'border-green-400',
    text: 'text-green-700',
    icon: '✅',
  },
  info: {
    bg: 'bg-blue-100',
    border: 'border-blue-400',
    text: 'text-blue-700',
    icon: 'ℹ️',
  },
  warning: {
    bg: 'bg-yellow-100',
    border: 'border-yellow-400',
    text: 'text-yellow-700',
    icon: '⚠️',
  },
  error: {
    bg: 'bg-red-100',
    border: 'border-red-400',
    text: 'text-red-700',
    icon: '❌',
  },
};

const Notification: React.FC<NotificationProps> = ({ message, type, duration = 5000, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => {
      clearTimeout(timer);
    };
  }, [duration, onClose]);

  const styles = notificationStyles[type];

  return (
    <div 
      className={`fixed top-20 right-5 max-w-sm w-full ${styles.bg} border-l-4 ${styles.border} ${styles.text} p-4 rounded-lg shadow-lg z-50`} 
      role="alert"
    >
      <div className="flex">
        <div className="py-1">
          <span className="text-2xl">{styles.icon}</span>
        </div>
        <div className="ml-3">
          <p className="font-bold">{message}</p>
        </div>
        <button onClick={onClose} className="ml-auto -mx-1.5 -my-1.5 bg-transparent rounded-lg focus:ring-2 focus:ring-gray-400 p-1.5 inline-flex h-8 w-8">
          <span className="sr-only">Close</span>
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
        </button>
      </div>
    </div>
  );
};

export default Notification;
