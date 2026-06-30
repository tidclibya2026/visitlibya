# Visit Libya Implementation Rules

These rules are mandatory for all future work on the Visit Libya project.

## Visual Identity

- Build a tourism-first visual identity. The interface must feel like a premium national tourism platform, not an internal government portal.
- Use the Figma Make design as the primary visual reference for layout, spacing, hierarchy, and component style.
- Follow the Figma Make design as the visual reference for visual hierarchy, page rhythm, cards, galleries, and premium tourism presentation.
- Maintain the Visit Libya visual language:
  - Mediterranean blue `#0B3A67`.
  - Desert gold `#C89B3C`.
  - Snow white `#F8FAFC`.
  - Oasis green `#2E7D5B`.
  - Heritage red `#8C2F22`.
  - Charcoal `#111827`.
  - Large expressive typography.
  - Premium destination cards.
  - Rich culture galleries.
  - Accurate Libya map usage only.
- Keep the design cinematic, welcoming, elegant, destination-focused, and visual-first.
- Preserve cinematic typography, white space, destination cards, cultural galleries, and the premium visual-first tourism style.

## Header And Footer

- The header must not include Ministry names, TIDC names, or long institutional labels.
- Header branding must remain tourism-oriented only, focused on Visit Libya and visitor navigation.
- Do not show Ministry or TIDC names in the header or hero sections.
- The Ministry of Tourism and Traditional Industries name may appear only in the footer.
- The Tourism Information & Documentation Center name may appear only in the footer.
- Ministry and Tourism Information & Documentation Center names must appear only in the footer.
- Footer text must remain official, clear, and consistent across pages.

## Images And Media

- Use local real Libyan images only from the project image folder.
- Do not use external placeholder images.
- Do not use Unsplash, remote stock photos, GitHub blob/tree links, or temporary external image URLs.
- Preserve the existing image folder name unless all paths are updated safely across HTML, CSS, and JavaScript.
- Check filename spelling, spaces, capitalization, and extensions carefully because GitHub Pages is case-sensitive.
- Do not distort images. Use professional cropping with `object-fit: cover` and stable aspect ratios.

## Content Integrity

- Do not change official text, page meaning, navigation labels, footer text, or existing content unless explicitly requested.
- Do not remove sections without explicit instruction.
- Do not replace local images with unrelated visuals.
- Do not introduce inaccurate maps, inaccurate Libya geography, or generic non-Libyan imagery.
- Use accurate Libya map assets only. Do not draw Libya boundaries manually.
- Do not delete existing content without reporting it.

## GitHub Pages Compatibility

- Keep the project static and GitHub Pages compatible.
- Use relative local paths for project files.
- Do not introduce React, backend services, build tools, package managers, or server-only dependencies unless explicitly requested.
- Do not create `rescue.css`, `css/style.css`, or `js/main.js`.
- Use the existing root-level `style.css` and `main.js`.
- Avoid broken links, missing assets, default blue links, horizontal overflow, and console errors.

## Implementation Process

- Before changing major files, explain the intended change clearly.
- Read the existing structure before editing.
- Keep changes scoped to the requested task.
- Report all changed files after implementation.
- Preserve current working functionality including navigation, VisitLibya AI, hero video behavior, filters, modals, and reveal effects.
- Verify relevant pages locally after implementation.
- When updating cache query strings, update all affected HTML pages consistently.
