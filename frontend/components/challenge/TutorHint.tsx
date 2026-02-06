"use client";

import React from 'react';

interface TutorHintProps {
  hint: string;
  level: number;
}

const TutorHint: React.FC<TutorHintProps> = ({ hint, level }) => {
  return (
    <div className="flex items-start gap-4 p-4 mt-4 bg-sky-50 border border-sky-200 rounded-xl">
      <div className="flex-shrink-0 h-2 w-2 rounded-full bg-sky-400 mt-2" />
      <div className="flex-grow">
        <p className="font-semibold text-sky-800">Tutor Hint #{level}</p>
        <p className="text-sky-700">{hint}</p>
      </div>
    </div>
  );
};

export default TutorHint;
