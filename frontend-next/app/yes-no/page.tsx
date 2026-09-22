import React from 'react';
import { YesNoExperience } from '../../components/YesNoExperience';

export const metadata = {
  title: 'KAVACH YES / NO | A deterministic yes or no',
  description:
    'Ask one clear yes or no question and receive a concise astrological indication with its explanation.',
};

export default function YesNoPage() {
  return <YesNoExperience />;
}
