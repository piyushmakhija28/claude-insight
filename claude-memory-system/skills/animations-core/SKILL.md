---
name: animations-core
description: Complete guidance for implementing animations using CSS, JavaScript, and animation libraries. Covers 2D/3D animations, UI animations, performance-aware design, and animation frameworks.
allowed-tools: Read,Glob,Grep,Bash,Edit,Write
user-invocable: true
---

# Animation Skill Instructions (CSS, JS, 2D, 3D, Frameworks)

### Skill Name
animations-core

### Description
This skill provides complete, production-grade guidance for implementing animations using CSS, JavaScript, and animation libraries. It covers 2D and 3D animations, UI animations, performance-aware animation design, and framework-based animation systems.

This skill is intended for real-world application development, not interview preparation.

---

## Animation Fundamentals

### 1. Core Animation Principles
- Time-based animation over frame-based logic
- Easing, duration, delay, and iteration control
- State-driven animation mindset
- Transform-based animation preference
- GPU acceleration awareness

---

## CSS Animations (Primary Tool)

### 2. CSS Animation Capabilities
- Transitions for simple state changes
- Keyframe animations for repeatable effects
- Transform properties (translate, scale, rotate, skew)
- Opacity-based animations
- Timing functions and cubic-bezier control
- Animation-fill-mode and direction handling

### When to Use CSS Animations
- Hover, focus, active states
- Simple UI feedback
- Small micro-interactions
- Performance-critical UI animations

---

## JavaScript Animations

### 3. JavaScript-Based Animation
- requestAnimationFrame usage
- State-controlled animations
- Timeline-based animation logic
- DOM, SVG, and Canvas animation awareness
- Synchronizing animation with user actions

### When to Use JavaScript Animations
- Complex sequences
- Dynamic values
- Scroll-based animations
- Chained or conditional animations

---

## CSS vs JavaScript Animation Decision Guide

### 4. Choosing the Right Tool
- Use CSS when animation is simple and declarative
- Use JavaScript when animation logic is dynamic
- Prefer CSS for performance and maintainability
- Prefer JS for control, orchestration, and complex timelines
- Avoid mixing CSS and JS on the same property unnecessarily

---

## Animation Libraries (Production Usage)

### 5. GSAP (Primary Advanced Tool)
- Timeline-based animation control
- Staggered animations
- Scroll-triggered animations
- Reusable animation sequences
- High-performance DOM and SVG animation

GSAP should be used when:
- CSS becomes hard to maintain
- Multiple animations must be coordinated
- Scroll and interaction-driven animations are required

---

## 2D Animation Techniques

### 6. 2D UI Animations
- Micro-interactions
- Loading indicators
- Skeleton loaders
- Button and card animations
- Modal and dropdown animations

Focus:
- Smoothness
- Feedback clarity
- Subtle motion

---

## 3D Animations (UI-Focused)

### 7. 3D Animation Concepts
- CSS 3D transforms
- Perspective and depth
- Parallax effects
- Card flip and layered UI animations
- Basic camera movement awareness

3D animations should enhance UI, not dominate it.

---

## Framework-Based Animations

### 8. Angular Animations
- Component enter and leave animations
- State-based animations
- Route-level animations
- Coordination between CSS and Angular animations
- Avoid over-animating structural directives

Angular animations should be:
- Predictable
- Maintainable
- Tied to component state

---

## Scroll & Interaction Animations

### 9. Interaction-Based Animations
- Scroll-driven animations
- Intersection Observer awareness
- Progressive reveal patterns
- Lazy animation loading
- Throttling and debouncing animation triggers

---

## Performance Optimization

### 10. Animation Performance Rules
- Animate transform and opacity only
- Avoid animating layout properties
- Reduce repaint and reflow
- Keep animation duration reasonable
- Optimize for mobile devices

---

## Accessibility & Motion Safety

### 11. Motion Accessibility
- Respect prefers-reduced-motion
- Avoid aggressive motion
- Ensure animations do not block usability
- Maintain visual clarity during transitions

---

## Animation Architecture

### 12. Organizing Animations
- Centralized animation utilities
- Reusable animation definitions
- Avoid animation duplication
- Separate animation logic from business logic

---

## Response Rules

- Prefer CSS animations by default
- Escalate to JS or GSAP only when needed
- Keep animations purposeful
- Optimize for performance and UX
- Provide clean, reusable animation patterns

---

## What Not to Do

- Do not over-animate UI
- Do not animate layout-heavy properties
- Do not mix multiple animation systems without reason
- Do not ignore performance and accessibility
- Do not create animations without user value

---

## Output Expectations

- Smooth and responsive animations
- Maintainable animation code
- Clear separation of concerns
- Real-world usable patterns
- Framework-friendly implementations

---

## Skill Scope

In scope:
- CSS animations
- JavaScript animations
- GSAP
- 2D UI animations
- 3D UI animations
- Angular animations
- Performance and accessibility

Out of scope:
- Game engines
- Film/VFX pipelines
- Native mobile animation APIs
- Low-level GPU programming

---

## Version
2.0.0