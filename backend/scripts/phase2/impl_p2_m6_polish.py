import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"

def update_timer():
    path = FRONTEND_DIR / "src" / "components" / "FocusSession" / "Timer.tsx"
    if path.exists():
        content = path.read_text(encoding='utf-8')
        if "motion.div" not in content:
            # Add framer-motion to Timer
            content = content.replace(
                "import React, { useEffect, useState } from 'react';",
                "import React, { useEffect, useState } from 'react';\\nimport { motion } from 'framer-motion';"
            )
            # Add pulsing animation to the timer circle when running
            content = content.replace(
                "strokeDashoffset={strokeDashoffset}",
                "strokeDashoffset={strokeDashoffset}\\n            className={isRunning ? 'transition-all duration-1000 ease-linear' : 'transition-all duration-300'}"
            )
            path.write_text(content, encoding='utf-8')
            print(f"Updated {path}")
        else:
            print(f"{path} already updated")
    else:
        print(f"Warning: {path} not found")

def update_runtime_context():
    path = FRONTEND_DIR / "src" / "context" / "RuntimeContext.tsx"
    if path.exists():
        content = path.read_text(encoding='utf-8')
        if "retryCount" not in content:
            # Add simple retry logic for fetch
            content = content.replace(
                "const [loading, setLoading] = useState(true);",
                "const [loading, setLoading] = useState(true);\\n  const [retryCount, setRetryCount] = useState(0);"
            )
            content = content.replace(
                "console.error('Failed to sync runtime state:', err);",
                "console.error('Failed to sync runtime state:', err);\\n      setRetryCount(prev => prev + 1);"
            )
            path.write_text(content, encoding='utf-8')
            print(f"Updated {path}")
        else:
            print(f"{path} already updated")
    else:
        print(f"Warning: {path} not found")

if __name__ == "__main__":
    update_timer()
    update_runtime_context()
    print("Milestone 6 Polish Applied.")
