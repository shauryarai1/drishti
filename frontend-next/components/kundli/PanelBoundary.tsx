'use client';

import React from 'react';

interface PanelBoundaryProps {
  children: React.ReactNode;
  label?: string;
}

interface PanelBoundaryState {
  failed: boolean;
}

// A failure inside one optional Kundli panel must never blank the whole page.
// This boundary keeps the error local and shows a clean message. It does not
// hide the error from logs.
export class PanelBoundary extends React.Component<PanelBoundaryProps, PanelBoundaryState> {
  state: PanelBoundaryState = { failed: false };

  static getDerivedStateFromError(): PanelBoundaryState {
    return { failed: true };
  }

  componentDidCatch(error: unknown) {
    if (typeof console !== 'undefined') {
      console.error('Kundli panel failed', error);
    }
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="rounded-lg border border-[#A62A34]/25 bg-[#160A0C]/70 p-4 text-[13px] text-[#EEE9DF]/70 sm:p-5">
          {this.props.label ? `${this.props.label} could not be displayed.` : 'This section could not be displayed.'}
        </div>
      );
    }
    return this.props.children;
  }
}
