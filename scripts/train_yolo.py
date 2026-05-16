# -*- coding: utf-8 -*-
"""
YOLO Object Detection Training Script
======================================
Train a YOLOv8 model on the Rice Leaf Disease Annotated Dataset.

Usage (from project root):
    python scripts/train_yolo.py              # Default: 25 epochs, yolov8n
    python scripts/train_yolo.py --epochs 5   # Quick test run
    python scripts/train_yolo.py --model yolov8s.pt --epochs 50  # Larger model

After training, the best weights will be saved to:
    runs/detect/train/weights/best.pt

Copy it to the models/ directory for deployment:
    copy runs\\detect\\train\\weights\\best.pt models\\yolov8_rice_leaf.pt
"""

import argparse
from pathlib import Path
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv8 on Rice Leaf Disease Dataset")
    parser.add_argument("--model", type=str, default="yolov8n.pt",
                        help="Base model to fine-tune (default: yolov8n.pt)")
    parser.add_argument("--epochs", type=int, default=25,
                        help="Number of training epochs (default: 25)")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Input image size (default: 640)")
    parser.add_argument("--batch", type=int, default=16,
                        help="Batch size (default: 16, reduce if GPU OOM)")
    parser.add_argument("--device", type=str, default=None,
                        help="Device: 'cuda', 'cpu', or device id like '0' (auto-detect if omitted)")
    args = parser.parse_args()

    # --- Resolve dataset path ---
    project_root = Path(__file__).resolve().parent.parent
    data_yaml = project_root / "RiceLeafAnnotatedDataset" / "data.yaml"

    if not data_yaml.exists():
        print(f"[ERROR] Dataset config not found: {data_yaml}")
        print("Please ensure the RiceLeafAnnotatedDataset folder is in the project root.")
        return

    print("=" * 60)
    print("  Rice Leaf Disease - YOLO Object Detection Training")
    print("=" * 60)
    print(f"  Base Model  : {args.model}")
    print(f"  Dataset     : {data_yaml}")
    print(f"  Epochs      : {args.epochs}")
    print(f"  Image Size  : {args.imgsz}")
    print(f"  Batch Size  : {args.batch}")
    print(f"  Device      : {args.device or 'auto'}")
    print("=" * 60)

    # --- Load pre-trained model and start training ---
    model = YOLO(args.model)

    results = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=str(project_root / "runs" / "detect"),
        name="train",
        exist_ok=True,
        pretrained=True,
        verbose=True,
    )

    # --- Summary ---
    best_weights = project_root / "runs" / "detect" / "train" / "weights" / "best.pt"
    print("\n" + "=" * 60)
    print("  Training Complete!")
    print("=" * 60)

    if best_weights.exists():
        print(f"  Best weights saved to: {best_weights}")
        print(f"\n  To deploy, copy the weights to the models/ directory:")
        print(f"    copy \"{best_weights}\" \"{project_root / 'models' / 'yolov8_rice_leaf.pt'}\"")
    else:
        print("  [WARN] best.pt not found. Training may have been interrupted.")

    print("=" * 60)


if __name__ == "__main__":
    main()
