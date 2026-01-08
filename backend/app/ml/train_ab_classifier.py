import os
from pathlib import Path
from typing import Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from app.ml.ab_classifier_model import ABClassifier


# Paths relative to this file
HERE = Path(__file__).resolve().parent
DATA_ROOT = HERE.parent / "data" / "ab_cells"          # app/data/ab_cells
WEIGHTS_PATH = HERE.parent / "models" / "ab_classifier.pth"  # app/models/ab_classifier.pth


def get_dataloaders(batch_size: int = 64) -> Tuple[DataLoader, DataLoader]:
    """
    Build train and validation dataloaders from:
      app/data/ab_cells/train/A, train/B, val/A, val/B
    """
    train_dir = DATA_ROOT / "train"
    val_dir = DATA_ROOT / "val"

    if not train_dir.exists() or not val_dir.exists():
        raise RuntimeError(f"Training/validation folders not found under {DATA_ROOT}")

    # Data augmentation for robustness
    train_transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((28, 28)),
        transforms.RandomRotation(5),
        transforms.RandomAffine(0, translate=(0.05, 0.05), scale=(0.95, 1.05)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5]),
    ])

    val_transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((28, 28)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5]),
    ])

    train_ds = datasets.ImageFolder(root=str(train_dir), transform=train_transform)
    val_ds = datasets.ImageFolder(root=str(val_dir), transform=val_transform)

    print("Classes (train):", train_ds.classes)  # should be ['A', 'B'] or ['B', 'A']

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    return train_loader, val_loader


def train_ab_classifier(
    epochs: int = 15,
    batch_size: int = 64,
    lr: float = 1e-3,
) -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    train_loader, val_loader = get_dataloaders(batch_size=batch_size)

    model = ABClassifier().to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0

        for images, labels in train_loader:
            images = images.to(device)
            # ImageFolder labels are 0/1 -> convert to float column vector
            labels = labels.float().unsqueeze(1).to(device)

            optimizer.zero_grad()
            outputs = model(images)          # [batch, 1]
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)

        epoch_loss = running_loss / len(train_loader.dataset)

        # ---- Validation ----
        model.eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)

                outputs = model(images)      # logits
                probs = torch.sigmoid(outputs).squeeze(1)    # [batch]
                preds = (probs >= 0.5).long()                # 0 or 1
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        val_acc = correct / total if total > 0 else 0.0
        print(f"Epoch {epoch:02d} - train_loss: {epoch_loss:.4f}  val_acc: {val_acc:.4f}")

        # Simple checkpointing
        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), WEIGHTS_PATH)
            print(f"  Saved best model to {WEIGHTS_PATH} (val_acc={val_acc:.4f})")

    print("Training completed. Best val_acc:", best_val_acc)
    print("Final weights should be at:", WEIGHTS_PATH)


if __name__ == "__main__":
    # You can tweak these numbers if needed
    train_ab_classifier(
        epochs=15,
        batch_size=64,
        lr=1e-3,
    )