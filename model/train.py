"""Train the YOLOv8n detector (classes: awake, asleep).

    python model/train.py --data path/to/data.yaml --epochs 50 --device 0

The dataset itself is not part of this repository.
"""

import argparse

from ultralytics import YOLO


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", required=True, help="dataset YAML (see model/data.example.yaml)")
    p.add_argument("--model", default="yolov8n.pt", help="starting weights (transfer learning)")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--device", default="0", help='GPU index, or "cpu"')
    p.add_argument("--workers", type=int, default=0, help="0 avoids dataloader crashes on Windows")
    args = p.parse_args()

    YOLO(args.model).train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
