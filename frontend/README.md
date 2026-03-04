# CloudManage Dashboard - Next.js Frontend

Modern, production-grade dashboard for Customer Success Digital FTE.

## Features

- 📊 **Dashboard** - KPIs, metrics, and channel statistics
- 🎫 **Tickets** - View and manage support tickets
- 👥 **Customers** - Customer management and history
- 📈 **Reports** - Analytics and insights
- 📝 **Web Form** - Submit support requests
- ⚙️ **Settings** - System configuration
- 🌙 **Dark Mode** - Light/dark theme support
- 📱 **Responsive** - Works on all devices

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios

## Installation

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on port 8001

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Edit .env and set API URL
NEXT_PUBLIC_API_URL=http://localhost:8001

# Start development server
npm run dev
```

### Open in Browser

```
http://localhost:3000
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout with sidebar
│   │   ├── page.tsx            # Dashboard page
│   │   ├── globals.css         # Global styles
│   │   ├── tickets/            # Tickets pages
│   │   ├── customers/          # Customer pages
│   │   ├── reports/            # Reports pages
│   │   └── webform/            # Web form page
│   ├── components/             # Reusable components
│   ├── lib/                    # Utilities
│   │   ├── api.ts              # API client
│   │   └── utils.ts            # Helper functions
│   └── types/                  # TypeScript types
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── next.config.js
```

## Available Scripts

```bash
# Development
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## API Integration

The frontend connects to the FastAPI backend:

```typescript
import { ticketsApi, customersApi } from '@/lib/api';

// Get ticket stats
const stats = await ticketsApi.getStats();

// Get all customers
const customers = await customersApi.getAll();
```

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Pages

### Dashboard (`/`)
- KPI cards (Total, Open, Resolved, Escalated tickets)
- Channel distribution
- Performance metrics
- System status

### Tickets (`/tickets`)
- List all tickets
- Filter by status, channel, priority
- Search functionality
- View ticket details
- Update status

### Customers (`/customers`)
- Customer list
- Search and filter
- Customer details
- Ticket history

### Reports (`/reports`)
- Volume charts
- Sentiment analysis
- Escalation trends
- Response time metrics

### Web Form (`/webform`)
- Submit support request
- Category selection
- Priority selection
- Confirmation with ticket number

### Settings (`/settings`)
- API keys status
- System health
- Configuration

## Component Examples

### KPI Card

```tsx
<KPICard
  title="Total Tickets"
  value={1234}
  icon={Ticket}
  color="bg-blue-500"
  trend="+12%"
  trendUp={true}
/>
```

### API Call

```tsx
const stats = await ticketsApi.getStats();
```

## Styling

Uses Tailwind CSS with custom primary color:

```tsx
className="bg-primary-600 hover:bg-primary-700"
```

## Dark Mode

Toggle dark mode in the sidebar. Uses `class` strategy:

```tsx
document.documentElement.classList.add('dark');
```

## Responsive Design

- Mobile: Sidebar hidden, hamburger menu
- Tablet: Optimized grid layouts
- Desktop: Full sidebar, multi-column layouts

## Performance

- Code splitting by route
- Image optimization
- Lazy loading
- Server-side rendering where appropriate

## Deployment

### Build

```bash
npm run build
```

### Start Production

```bash
npm start
```

### Docker (Optional)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit PR

## License

MIT
