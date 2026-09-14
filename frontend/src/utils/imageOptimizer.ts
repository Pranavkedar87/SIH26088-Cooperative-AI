/**
 * Image optimization utility for Citizen document scanning.
 *
 * Compresses and downscales photos client-side to preserve mobile/rural
 * bandwidth while maintaining sufficient visual clarity for Gemini OCR.
 *
 * Phase 3C.3 — exported constants allow callers to validate sizes before
 * and after optimization without duplicating magic numbers.
 */

// ── Configurable defaults (Phase 3C.3) ────────────────────────────────────────

/** Maximum dimension (width or height) of the output image in pixels. */
export const IMAGE_MAX_DIM = 1600;

/** JPEG encoding quality — high enough for readable document text. */
export const IMAGE_QUALITY = 0.82;

/** Backend hard limit (5 MB). Callers must reject blobs above this. */
export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

// ── Core optimizer ─────────────────────────────────────────────────────────────

/**
 * Compress and resize a Blob to a JPEG suitable for document analysis.
 *
 * Guarantees:
 * - Never upscales small images (output ≤ input dimensions).
 * - Longest dimension ≤ maxDim.
 * - Transparent PNGs receive a white background before JPEG conversion.
 * - Temporary object URLs are revoked immediately after use.
 * - ImageBitmap (where supported) respects EXIF orientation automatically.
 * - Falls back to <img> element in environments where createImageBitmap is
 *   unavailable (older Safari, certain WebViews).
 *
 * EXIF orientation note:
 *   createImageBitmap with { imageOrientation: "from-image" } corrects
 *   orientation in Chrome ≥ 84 and Safari ≥ 15.4.  The <img> fallback also
 *   auto-orients in modern browsers via CSS image-orientation.  No third-party
 *   library is required; EXIF parsing is handled by the browser itself.
 *
 * @param file    Source image Blob (JPEG / PNG / WebP).
 * @param maxDim  Longest edge in pixels. Default: IMAGE_MAX_DIM (1600).
 * @param quality JPEG quality 0–1. Default: IMAGE_QUALITY (0.82).
 */
export async function compressAndResizeImage(
  file: Blob,
  maxDim: number = IMAGE_MAX_DIM,
  quality: number = IMAGE_QUALITY
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    if (!file || !(file instanceof Blob) || file.size === 0) {
      return reject(new Error("Invalid or empty image file provided for optimization."));
    }

    // Primary path: createImageBitmap (Chrome, Firefox, Safari ≥ 15.4)
    if (typeof createImageBitmap === "function") {
      createImageBitmap(file, { imageOrientation: "from-image" } as any)
        .then((bitmap) => {
          try {
            const result = _renderToJpeg(bitmap, bitmap.width, bitmap.height, maxDim, quality);
            bitmap.close(); // release GPU memory
            result.then(resolve).catch(reject);
          } catch (err) {
            bitmap.close();
            reject(err);
          }
        })
        .catch(() => {
          // Fallback to <img> element (older Safari / WebViews)
          _fallbackImageElement(file, maxDim, quality, resolve, reject);
        });
    } else {
      _fallbackImageElement(file, maxDim, quality, resolve, reject);
    }
  });
}

// ── Internal helpers ───────────────────────────────────────────────────────────

/**
 * Draw source image onto a canvas and serialise to JPEG blob.
 * Used by both the ImageBitmap path and the <img> fallback.
 */
function _renderToJpeg(
  source: HTMLImageElement | ImageBitmap,
  srcWidth: number,
  srcHeight: number,
  maxDim: number,
  quality: number
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    // Compute target dimensions — never upscale
    let targetWidth = srcWidth;
    let targetHeight = srcHeight;

    if (srcWidth > maxDim || srcHeight > maxDim) {
      if (srcWidth >= srcHeight) {
        targetWidth = maxDim;
        targetHeight = Math.round((srcHeight * maxDim) / srcWidth);
      } else {
        targetHeight = maxDim;
        targetWidth = Math.round((srcWidth * maxDim) / srcHeight);
      }
    }

    const canvas = document.createElement("canvas");
    canvas.width = targetWidth;
    canvas.height = targetHeight;
    const ctx = canvas.getContext("2d");

    if (!ctx) {
      return reject(new Error("Failed to initialise Canvas 2D context for image optimisation."));
    }

    // White background — handles transparent PNGs cleanly
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, targetWidth, targetHeight);
    ctx.drawImage(source as any, 0, 0, targetWidth, targetHeight);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject(new Error("Canvas failed to serialise optimised image blob."));
        }
      },
      "image/jpeg",
      quality
    );
  });
}

/**
 * Fallback for environments without createImageBitmap.
 * Uses an <img> element with a temporary object URL.
 */
function _fallbackImageElement(
  file: Blob,
  maxDim: number,
  quality: number,
  resolve: (blob: Blob) => void,
  reject: (err: Error) => void
): void {
  // In pure Node test environments, URL / Image may not exist — pass through.
  if (typeof URL === "undefined" || typeof Image === "undefined") {
    return resolve(file);
  }

  const url = URL.createObjectURL(file);
  const img = new Image();

  img.onload = () => {
    URL.revokeObjectURL(url); // release immediately after load
    _renderToJpeg(img, img.naturalWidth, img.naturalHeight, maxDim, quality)
      .then(resolve)
      .catch(reject);
  };

  img.onerror = () => {
    URL.revokeObjectURL(url);
    reject(new Error("Failed to load image for optimisation. The file may be corrupt."));
  };

  img.src = url;
}
