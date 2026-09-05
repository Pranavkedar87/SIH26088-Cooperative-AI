declare module "jspdf" {
  export class jsPDF {
    constructor(options?: any);
    addImage(
      imageData: string,
      format: string,
      x: number,
      y: number,
      w: number,
      h: number
    ): void;
    addPage(): void;
    save(filename: string): void;
  }
  export default jsPDF;
}

declare module "html2canvas" {
  export default function html2canvas(
    element: HTMLElement,
    options?: any
  ): Promise<HTMLCanvasElement>;
}
