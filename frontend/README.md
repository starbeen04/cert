# CertFast Frontend

A Vue.js 3 admin dashboard for the CertFast certificate processing system.

## Features

- **Vue 3 + TypeScript**: Modern frontend framework with type safety
- **Element Plus**: Professional UI component library
- **Vue Router**: Client-side routing
- **Pinia**: State management
- **Axios**: HTTP client for API communication
- **Vite**: Fast build tool and development server

## Admin Dashboard Features

- **Authentication**: JWT-based login system
- **User Management**: Create, edit, and manage users
- **Certificate Management**: Upload, process, and manage PDF certificates
- **AI Agent Management**: Configure and monitor AI agents
- **PDF Upload**: Drag-and-drop PDF upload with progress tracking
- **Statistics Dashboard**: Real-time system metrics and analytics
- **Responsive Design**: Mobile-first responsive layout

## Development Setup

### Prerequisites

- Node.js 16+ and npm
- Backend API running on port 8100

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3100`

### Build for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/          # Reusable Vue components
├── layouts/            # Layout components
│   └── AdminLayout.vue # Main admin layout with sidebar
├── router/             # Vue Router configuration
├── services/           # API service layer
│   └── api.ts         # Axios HTTP client
├── stores/            # Pinia state management
│   ├── auth.ts        # Authentication store
│   ├── users.ts       # User management store
│   ├── certificates.ts # Certificate management store
│   ├── aiAgents.ts    # AI agent management store
│   └── dashboard.ts   # Dashboard statistics store
├── styles/            # Global styles
├── types/             # TypeScript type definitions
├── utils/             # Utility functions
├── views/             # Page components
│   ├── auth/          # Authentication pages
│   ├── dashboard/     # Dashboard pages
│   ├── users/         # User management pages
│   ├── certificates/  # Certificate management pages
│   ├── ai-agents/     # AI agent management pages
│   ├── upload/        # PDF upload pages
│   ├── monitoring/    # Statistics and monitoring pages
│   ├── profile/       # User profile pages
│   └── error/         # Error pages
├── App.vue            # Root component
└── main.ts            # Application entry point
```

## Environment Variables

Create a `.env` file in the root directory:

```
VITE_API_BASE_URL=http://localhost:8100
VITE_APP_TITLE=CertFast Admin
```

## API Integration

The frontend communicates with the FastAPI backend through:

- **Base URL**: `http://localhost:8100`
- **Authentication**: JWT tokens
- **API Proxy**: Vite dev server proxies `/api` requests to the backend

## Key Technologies

- **Vue 3**: Composition API, TypeScript support
- **Element Plus**: UI components with auto-import
- **Vue Router**: Page routing with authentication guards
- **Pinia**: Centralized state management
- **Axios**: HTTP client with interceptors
- **Vite**: Build tool with HMR

## Admin Features

### Dashboard
- System overview with key metrics
- Real-time statistics
- Quick action buttons
- Recent activity feed

### User Management
- User listing with search and filters
- Create/edit/delete users
- User detail pages with activity history
- Role management (Admin/User)

### Certificate Management
- Certificate listing with status tracking
- PDF upload with progress indicators
- Certificate processing workflow
- Download and view certificates

### AI Agent Management
- Configure AI models and prompts
- Test agent responses
- Monitor agent performance
- Enable/disable agents

### Monitoring
- System performance metrics
- Request analytics
- Component status monitoring
- Activity logs and alerts

## Development Guidelines

- Use Composition API for Vue components
- Implement TypeScript for type safety
- Follow Element Plus design patterns
- Use Pinia for state management
- Implement responsive design
- Add loading states and error handling
- Include accessibility features

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2020+ features required
- Mobile responsive design