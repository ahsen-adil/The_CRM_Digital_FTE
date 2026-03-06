---
name: frontend-3d-design
description: Generate modern 3D animated frontend interfaces using Three.js, glassmorphism UI, neon glow effects, and GPU-optimized animations for React and modern web apps.
---

# Frontend 3D Design Skill

This skill helps generate visually advanced UI/UX with:

- Three.js scenes
- particle backgrounds
- glassmorphism UI
- neon glow aesthetic
- GPU accelerated animations
- modern React components

Use this skill when building:

- landing pages
- SaaS dashboards
- futuristic UI
- portfolio websites
- AI product interfaces
- WebGL hero sections

---

# Tech Stack

Preferred technologies:

- Three.js r128
- React + JSX
- Canvas API
- CSS3D transforms
- Intersection Observer
- GPU accelerated CSS transforms

---

# Design Aesthetic

Use this style system:

Theme:
- Dark mode first
- Futuristic neon glow
- Glassmorphism cards
- Floating particle backgrounds

Primary colors:

- Neon teal `#00f0c8`
- Neon violet `#7c3aed`
- Deep background `#020817`

---

# Core Capabilities

The skill should help generate:

### 1 Three.js Scenes
Create lightweight 3D hero elements.

Example objects:
- wireframe spheres
- floating particles
- abstract geometry
- glowing grids

Scene structure:

- Scene
- PerspectiveCamera
- WebGLRenderer
- Mesh geometry
- Animation loop

---

### 2 Particle Systems

Generate animated particles with:

- buffer geometry
- additive blending
- low GPU load
- depth illusion

Use particle counts:

- Hero background → 2000 particles
- Section background → 300–800

---

### 3 Glassmorphism UI

Cards must include:

- backdrop blur
- translucent background
- subtle border
- soft shadows

Example properties:

blur: 20px  
opacity: 0.05  
border radius: 24px  

---

### 4 Neon Glow Effects

Glow styles:

- neon text
- glowing borders
- radial gradient orbs
- accent highlights

Colors:

- teal glow
- violet glow
- amber accent

---

### 5 Motion System

Use smooth motion:

Preferred easing:

cubic-bezier(0.23,1,0.32,1)

Animations include:

- floating motion
- glow pulse
- gradient shift
- reveal on scroll

---

### 6 Scroll Reveal Animations

Use Intersection Observer.

Animation pattern:

1. element hidden
2. enter viewport
3. fade + slide up

Duration:

600–800ms

---

### 7 Floating Orb Backgrounds

Use blurred radial gradients.

Example sizes:

- small orb → 200px
- large orb → 400px

Animation:

slow floating loop

---

### 8 GPU Optimization

Always optimize performance:

Use:

translate3d  
requestAnimationFrame  
memoized React components

Avoid:

layout thrashing  
heavy shadow DOM

---

# Component Patterns

Generate reusable components such as:

AnimatedCounter  
ProgressRing  
GlassCard  
Hero3DScene  
ParticleBackground  

---

# Mobile Responsiveness

Design rules:

grid:

auto-fit minmax(300px,1fr)

breakpoint:

768px mobile

Disable heavy 3D effects on low power devices.

---

# Accessibility

Include:

focus states  
reduced motion support  
semantic HTML

---

# Output Style

When generating UI code:

1. React components preferred
2. modular CSS
3. GPU optimized animation
4. production ready structure
5. minimal dependencies

---

# Example Requests

Examples where this skill should be used:

- "Create a futuristic SaaS landing page"
- "Build a 3D hero section with particles"
- "Make glassmorphism dashboard UI"
- "Add neon glow WebGL background"