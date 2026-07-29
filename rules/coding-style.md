# Coding Style

## Principles

1. **Immutability** — Prefer const/let over var, avoid mutation
2. **Small functions** — Each function does one thing
3. **Clear names** — Variables and functions describe their purpose
4. **Early returns** — Avoid deep nesting
5. **No magic numbers** — Use named constants

## File Organization

```
src/
├── components/     # UI components
├── hooks/          # Custom hooks
├── services/       # API calls
├── utils/          # Helper functions
├── types/          # TypeScript types
└── index.ts        # Entry point
```

## Imports

```typescript
// 1. External libraries
import React from 'react'
import axios from 'axios'

// 2. Internal modules
import { formatDate } from '../utils/date'
import { User } from '../types/user'

// 3. Components
import { Button } from './Button'
```
