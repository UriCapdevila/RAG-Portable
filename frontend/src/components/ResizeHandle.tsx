import { useCallback, useEffect, useRef, useState } from "react";

type ResizeHandleProps = {
  /** Which side of the chat this handle is on */
  side: "left" | "right";
  /** Current width of the panel being resized */
  currentWidth: number;
  /** Callback to update the panel width */
  onResize: (newWidth: number) => void;
  /** Minimum allowed width */
  minWidth?: number;
  /** Maximum allowed width */
  maxWidth?: number;
};

export default function ResizeHandle({
  side,
  currentWidth,
  onResize,
  minWidth = 200,
  maxWidth = 480,
}: ResizeHandleProps) {
  const [isDragging, setIsDragging] = useState(false);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsDragging(true);
      startXRef.current = e.clientX;
      startWidthRef.current = currentWidth;
    },
    [currentWidth],
  );

  useEffect(() => {
    if (!isDragging) return;

    function handleMouseMove(e: MouseEvent) {
      const delta = e.clientX - startXRef.current;
      // Left handle: dragging right = bigger panel, dragging left = smaller
      // Right handle: dragging left = bigger panel, dragging right = smaller
      const newWidth =
        side === "left"
          ? startWidthRef.current + delta
          : startWidthRef.current - delta;

      const clamped = Math.max(minWidth, Math.min(maxWidth, newWidth));
      onResize(clamped);
    }

    function handleMouseUp() {
      setIsDragging(false);
    }

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    // Prevent text selection while dragging
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
    };
  }, [isDragging, side, minWidth, maxWidth, onResize]);

  return (
    <div
      className={`resize-handle ${isDragging ? "resize-handle-active" : ""}`}
      onMouseDown={handleMouseDown}
      role="separator"
      aria-orientation="vertical"
      aria-label={`Redimensionar panel ${side === "left" ? "izquierdo" : "derecho"}`}
      tabIndex={0}
    >
      <div className="resize-handle-indicator" />
    </div>
  );
}
