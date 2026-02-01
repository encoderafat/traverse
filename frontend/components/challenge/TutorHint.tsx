"use client";

import React from 'react';

interface TutorHintProps {
  hint: string;
  level: number;
}

const TutorHint: React.FC<TutorHintProps> = ({ hint, level }) => {
  return (
    <div className="flex items-start gap-4 p-4 mt-4 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex-shrink-0 text-2xl">
        🧠
      </div>
      <div className="flex-grow">
        <p className="font-semibold text-blue-800">Tutor Hint #{level}</p>
        <p className="text-blue-700">{hint}</p>
      </div>
    </div>
  );
};

export default TutorHint;
