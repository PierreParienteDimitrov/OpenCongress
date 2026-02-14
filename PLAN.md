# Plan: Integrate assistant-ui + Floating Draggable Chat Panel

## Overview
Replace the current hand-rolled Sheet-based chat with `@assistant-ui/react` for rich chat UX (streaming, markdown, code blocks, copy, edit, regenerate), wrapped in a **floating draggable/resizable panel** using framer-motion (already installed).

The Django backend requires **zero changes** — the existing SSE endpoint works as-is.

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `frontend/package.json` | Add `@assistant-ui/react`, `@assistant-ui/react-markdown`, `remark-gfm` |
| `frontend/src/components/assistant-ui/thread.tsx` | **New** — shadcn-installed Thread component (via CLI) |
| `frontend/src/components/assistant-ui/markdown-text.tsx` | **New** — shadcn-installed markdown renderer (via CLI) |
| `frontend/src/components/assistant-ui/tooltip-icon-button.tsx` | **New** — shadcn-installed helper (via CLI) |
| `frontend/src/components/chat/ChatModelAdapter.ts` | **New** — Django SSE adapter for assistant-ui LocalRuntime |
| `frontend/src/components/chat/ChatInterface.tsx` | **Rewrite** — Floating panel wrapping assistant-ui Thread |
| `frontend/src/app/globals.css` | Add assistant-ui markdown styles import |

---

## Step-by-Step Implementation

### Step 1: Install dependencies

```bash
cd frontend
npm install @assistant-ui/react @assistant-ui/react-markdown remark-gfm
```

### Step 2: Install assistant-ui shadcn components

```bash
npx shadcn@latest add https://r.assistant-ui.com/thread
```

This scaffolds `thread.tsx`, `markdown-text.tsx`, and `tooltip-icon-button.tsx` into `src/components/assistant-ui/`. These are source files we own and can customize.

### Step 3: Add CSS import for markdown styles

In `globals.css`, add:
```css
@import "@assistant-ui/react-markdown/styles/dot.css";
```

### Step 4: Create ChatModelAdapter (`ChatModelAdapter.ts`)

This is the bridge between assistant-ui's LocalRuntime and our Django SSE backend. Key design:

```typescript
import { ChatModelAdapter } from "@assistant-ui/react";

export function createDjangoChatAdapter(
  provider: string,
  pageContext: PageContext | null,
): ChatModelAdapter {
  return {
    async *run({ messages, abortSignal }) {
      // 1. Get session token
      // 2. POST to /auth/chat/stream/ with provider, messages, page_context
      // 3. Parse SSE chunks (data: {chunk: "..."})
      // 4. yield { content: [{ type: "text", text: cumulativeText }] }
      //    (assistant-ui expects cumulative text, not deltas)
      // 5. Pass abortSignal to fetch for cancel support
    },
  };
}
```

- Uses `async *run()` generator for streaming
- Each `yield` provides **cumulative** text content
- `abortSignal` passed to `fetch()` for built-in cancel
- Throws on `data.error` — assistant-ui displays errors automatically
- No changes to Django backend needed

### Step 5: Customize assistant-ui Thread component

Edit the scaffolded `thread.tsx` to:
- Remove the default outer container/frame (we provide our own floating panel)
- Style messages to match our Bloomberg-inspired theme:
  - User bubbles: `bg-primary text-primary-foreground`
  - Assistant bubbles: `bg-secondary text-secondary-foreground`
- Customize empty state to show contextual message ("Ask me anything about this bill / this vote / congressional activity")
- Customize composer to match current input styling
- Keep built-in features: markdown, code blocks, copy button, regenerate, edit, auto-scroll

### Step 6: Rewrite ChatInterface.tsx — Floating Panel + assistant-ui

Replace the Sheet-based component with a floating draggable panel. Structure:

```
<>
  {/* FAB trigger button — same as now */}
  <Button onClick={toggle} className="fixed bottom-6 right-6 z-50 ..." />

  {/* Floating panel */}
  <AnimatePresence>
    {isOpen && (
      <motion.div
        key={panelKey}
        drag
        dragControls={dragControls}
        dragListener={false}        // header-only drag
        dragMomentum={false}
        dragConstraints={...}       // viewport bounds
        onDragEnd={foldOffsetIntoState}
        initial/animate/exit={fadeScale}
        style={{ position: fixed, left, top, width, height, zIndex: 50 }}
        className="flex flex-col rounded-lg border bg-background shadow-xl"
      >
        {/* Drag header */}
        <div onPointerDown={dragControls.start}>
          <h2>AI Assistant</h2>
          <provider badges>
          <buttons: clear | reset | close>
        </div>

        {/* assistant-ui runtime + thread */}
        <AssistantRuntimeProvider runtime={localRuntime}>
          <Thread />   {/* ← assistant-ui handles everything inside */}
        </AssistantRuntimeProvider>

        {/* Resize handles (SE corner, E edge, S edge) */}
      </motion.div>
    )}
  </AnimatePresence>
</>
```

**Panel behavior** (same as your spec):
- `DEFAULT_WIDTH = 400`, `DEFAULT_HEIGHT = 560`, `MIN_WIDTH = 320`, `MIN_HEIGHT = 400`
- Default position: bottom-right, above trigger button
- Header-only drag via `dragListener={false}` + `dragControls`
- Resize via mousedown/mousemove/mouseup on handles (SE corner with grip dots, E/S edges invisible)
- `panelKey` incremented on reset to force re-mount (resets framer-motion transform)
- `onDragEnd` folds offset into `panelPosition` state
- Window resize listener clamps position within viewport
- Mobile (<640px): full-screen, no drag/resize

**Header buttons** (ghost variant, icon-xs size):
- Clear chat → `switchToNewThread()` via assistant-ui API
- Reset position/size → resets state + increments panelKey
- Close → `setIsOpen(false)`

**Provider selection**: Badge row in header (same as current). The selected provider is passed to the ChatModelAdapter which is rebuilt via `useMemo` when provider changes.

**API keys / no-keys state**: Handled outside assistant-ui — if no keys configured, show the "Go to Settings" prompt instead of the Thread.

**Page context**: `useChatContext()` hook value passed to adapter, so the Django backend still receives context about the current page.

### Step 7: Clean up

- Remove `Sheet`, `SheetContent`, `SheetHeader`, `SheetTitle`, `SheetTrigger` imports from ChatInterface (no longer used anywhere)
- The `streamChat` function in `api-client.ts` can be kept (other code might use it) or marked for removal if unused
- Existing `chat-context.tsx` stays unchanged — still used by page components

---

## What assistant-ui Gives Us (vs current hand-rolled)

| Feature | Current | With assistant-ui |
|---------|---------|-------------------|
| Streaming | Manual chunk accumulation | Built-in, auto-scroll |
| Markdown rendering | None (plain `whitespace-pre-wrap`) | Full GFM markdown + code highlighting |
| Copy message | No | Built-in copy button |
| Edit user message | No | Built-in edit + re-send |
| Regenerate response | No | Built-in regenerate button |
| Cancel generation | No | Built-in cancel (uses AbortSignal) |
| Branch navigation | No | Built-in branch picker |
| Message state management | Manual useState | Automatic via LocalRuntime |
| Keyboard shortcuts | Enter to send only | Full set |

## What Stays the Same

- Django backend: zero changes
- `chat-context.tsx`: unchanged
- `api-client.ts`: `streamChat` stays (adapter uses raw fetch instead, but the function remains available)
- FAB trigger button position and appearance
- Provider badge selection UX
- No-keys "Go to Settings" prompt
- Page context awareness

## Verification

1. `npm run build` — no type/build errors
2. Open browser → log in → click chat button → floating panel appears (no overlay)
3. Drag header → panel moves, constrained to viewport
4. Resize corner/edges → respects min dimensions
5. Send message → streams with markdown rendering
6. Copy/edit/regenerate buttons work
7. Cancel mid-stream works
8. Clear chat resets to empty state
9. Reset button snaps panel to default position/size
10. Provider switching works
11. Page context displayed in empty state ("Ask me about this bill")
12. Mobile (<640px) → full-screen mode
13. Window resize → panel stays within bounds
