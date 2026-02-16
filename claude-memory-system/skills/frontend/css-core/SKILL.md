---
name: css-core
description: Comprehensive guidance for writing, understanding, and maintaining CSS across modern web applications. Covers CSS concepts, responsive design, modern layout systems, and CSS frameworks.
allowed-tools: Read,Glob,Grep,Bash,Edit,Write
user-invocable: true
---

# CSS (Cascading Style Sheets) Skill Instructions

### Skill Name
css-core

### Description
This skill provides comprehensive guidance for writing, understanding, and maintaining CSS across modern web applications. It covers core CSS concepts, multiple types of CSS usage, responsive design, modern layout systems, and popular CSS frameworks.

This skill applies to framework-agnostic CSS as well as CSS usage in Angular and other frontend frameworks.

---

## Core CSS Knowledge

### 1. CSS Fundamentals
- Box model (content, padding, border, margin)
- CSS selectors (element, class, id, attribute)
- Combinators (descendant, child, sibling)
- Pseudo-classes and pseudo-elements
- Specificity and cascade rules
- Inheritance behavior

### 2. Types of CSS (Very Important)
- Inline CSS
- Internal (embedded) CSS
- External CSS
- Component-scoped CSS
- Global CSS
- Modular CSS

---

## Layout Systems

### 3. Modern Layout Techniques
- Flexbox (one-dimensional layouts)
- CSS Grid (two-dimensional layouts)
- Positioning (static, relative, absolute, fixed, sticky)
- Float-based layouts (legacy awareness)
- Z-index and stacking context

---

## Responsive Design

### 4. Responsive & Adaptive CSS
- Media queries
- Mobile-first design
- Fluid layouts
- Responsive units (%, vw, vh, rem, em)
- Breakpoint strategies

---

## Modern CSS Features

### 5. Advanced & Modern CSS
- CSS variables (custom properties)
- calc(), clamp(), min(), max()
- Transitions and animations
- Keyframes
- Object-fit and aspect-ratio
- Modern selectors (:is, :where, :has awareness)

---

## CSS Architecture & Methodologies

### 6. CSS Structuring Approaches
- BEM (Block Element Modifier)
- OOCSS
- SMACSS
- Utility-first CSS concepts
- Component-based styling approach

---

## Frameworks & Libraries

### 7. CSS Frameworks (Must Know)
- Bootstrap
- Tailwind CSS
- Bulma
- Foundation
- Material UI (CSS layer awareness)
- PrimeFlex
- Angular Material theming concepts

Frameworks should be used responsibly and customized where needed.

---

## CSS in Angular Context

### 8. Angular-Specific CSS Concepts
- Component-level styles
- Global styles (styles.css / styles.scss)
- View encapsulation (Emulated, None, Shadow DOM)
- CSS isolation and leakage prevention
- Styling Angular Material components
- Overriding framework styles safely

---

## Preprocessors & Extensions

### 9. CSS Preprocessors
- SCSS / Sass
- Variables, mixins, nesting
- Partials and imports
- Avoid deep nesting
- Maintain readability

---

## Performance & Best Practices

### 10. Performance Considerations
- Minimize unused CSS
- Avoid overly complex selectors
- Reduce layout thrashing
- Reusable utility classes
- Keep CSS scalable and maintainable

---

## Accessibility & UX

### 11. Accessible Styling
- Color contrast awareness
- Focus states
- Hover vs focus behavior
- Readable font sizes
- Responsive typography

---

## Response Rules

- Write clean, readable, maintainable CSS
- Prefer modern CSS over legacy techniques
- Explain CSS behavior briefly when relevant
- Avoid framework lock-in unless requested
- Provide practical, real-world examples

---

## What Not to Do

- Do not rely heavily on !important
- Do not write deeply nested selectors
- Do not mix layout and styling responsibilities unnecessarily
- Do not ignore responsiveness
- Do not assume fixed screen sizes

---

## Output Expectations

- Well-structured CSS
- Framework-agnostic styling by default
- Modern layout techniques
- Angular-compatible CSS examples
- Interview-ready explanations

---

## Skill Scope

In scope:
- Core CSS
- Modern CSS
- CSS frameworks
- Angular styling concepts
- Responsive and accessible design

Out of scope:
- JavaScript logic
- Build tools configuration
- Browser engine internals
- Design tools

---

## Version
1.0.0