/**
 * Image optimization utility for Citizen document scanning.
 * Compresses and downscales photos client-side to preserve mobile/rural bandwidth
 * while maintaining high visual clarity for OCR analysis.
 */

export async function compressAndResizeImage(
  file: Blob,
  maxDim: number = 1600,
  quality: number = 0.82
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    if (!file || !(file instanceof Blob) || file.size === 0) {
      return reject(new Error("Invalid or empty image file provided for optimization."));
    }

    // In environments with createImageBitmap (modern Chrome/Safari/Firefox),
    // imageOrientation: 'from-image' respects EXIF orientation automatically.
    if (typeof createImageBitmap === "function") {
      createImageBitmap(file, { imageOrientation: "from-image" } as any)
        .then((bitmap) => {
          try {
            const { width, height } = bitmap;
            let targetWidth = width;
            let targetHeight = height;

            // Only downscale if larger than maxDim, never upscale small images
            if (width > maxDim || height > maxDim) {
              if (width >= height) {
                targetWidth = maxDim;
                targetHeight = Math.round((height * maxDim) / width);
              } else {
                targetHeight = maxDim;
                targetWidth = Math.round((width * maxDim) / height);
              }
            }

            const canvas = document.createElement("canvas");
            canvas.width = targetWidth;
            canvas.height = targetHeight;
            const ctx = canvas.getContext("2d");
            if (!ctx) {
              bitmap.close();
              return reject(new Error("Failed to initialize canvas context for image optimization."));
            }

            // Fill white background (handles transparent PNGs converting to JPEG)
            ctx.fillStyle = "#FFFFFF";
            ctx.fillRect(0, 0, targetWidth, targetHeight);
            ctx.drawImage(bitmap, 0, 0, targetWidth, targetHeight);
            bitmap.close();

            canvas.toBlob(
              (blob) => {
                if (blob) {
                  resolve(blob);
                } else {
                  reject(new Error("Canvas failed to serialize optimized image blob."));
                }
              },
              "image/jpeg",
              quality
            );
          } catch (err) {
            bitmap.close();
            reject(err);
          }
        })
        .catch(() => {
          // Fallback to standard Image element if createImageBitmap throws
          fallbackImageElement(file, maxDim, quality, resolve, reject);
        });
    } else {
      fallbackImageElement(file, maxDim, quality, resolve, reject);
    }
  });
}

function fallbackImageElement(
  file: Blob,
  maxDim: number,
  quality: number,
  resolve: (blob: Blob) => void,
  reject: (err: Error) => void
) {
  // If running in an environment without DOM URL (e.g. mock test), reject or return
  if (typeof URL === "undefined" || typeof Image === "undefined") {
    return resolve(file);
  }

  const url = URL.createObjectURL(file);
  const img = new Image();

  img.onload = () => {
    URL.revokeObjectURL(url);
    try {
      const { naturalWidth: width, naturalHeight: height } = img;
      let targetWidth = width;
      let targetHeight = height;

      if (width > maxDim || height > maxDim) {
        if (width >= height) {
          targetWidth = maxDim;
          targetHeight = Math.round((height * maxDim) / width);
        } else {
          targetHeight = maxDim;
          targetWidth = Math.round((width * maxDim) / height);
        }
      }

      const canvas = document.createElement("canvas");
      canvas.width = targetWidth;
      canvas.height = targetHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        return reject(new Error("Failed to get canvas 2D context in fallback."));
      }

      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, targetWidth, targetHeight);
      ctx.drawImage(img, 0, 0, targetWidth, targetHeight);

      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error("Canvas fallback failed to produce optimized blob."));
          }
        },
        "image/jpeg",
        quality
      );
    } catch (err: any) {
      reject(err instanceof Error ? err : new Error(String(err)));
    }
  };

  img.onerror = () => {
    URL.revokeObjectURL(url);
    reject(new Error("Failed to load image for optimization."));
  };

  img.src = url;
}
