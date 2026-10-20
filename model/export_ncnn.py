"""Export trained weights to NCNN for fast CPU inference on a Raspberry Pi.

    python model/export_ncnn.py --weights runs/detect/train/weights/best.pt

Produces a `best_ncnn_model/` folder next to the weights.
"""

import argparse

from ultralytics import YOLO


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--weights", required=True, help="trained .pt file")
    p.add_argument("--imgsz", type=int, default=640)
    args = p.parse_args()

    out = YOLO(args.weights).export(format="ncnn", imgsz=args.imgsz)
    print(f"NCNN model written to: {out}")


if __name__ == "__main__":
    main()
