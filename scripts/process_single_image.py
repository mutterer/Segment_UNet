import argparse
from pathlib import Path

import numpy as np
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F


class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class UNetSmall(nn.Module):
    def __init__(self, in_ch=1, out_ch=1, base=32):
        super().__init__()
        self.enc1 = DoubleConv(in_ch, base)
        self.pool1 = nn.MaxPool2d(2)

        self.enc2 = DoubleConv(base, base * 2)
        self.pool2 = nn.MaxPool2d(2)

        self.enc3 = DoubleConv(base * 2, base * 4)
        self.pool3 = nn.MaxPool2d(2)

        self.bottleneck = DoubleConv(base * 4, base * 8)

        self.up3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
        self.dec3 = DoubleConv(base * 8, base * 4)

        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
        self.dec2 = DoubleConv(base * 4, base * 2)

        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
        self.dec1 = DoubleConv(base * 2, base)

        self.outc = nn.Conv2d(base, out_ch, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))
        b = self.bottleneck(self.pool3(e3))

        d3 = self.up3(b)
        if d3.shape[-2:] != e3.shape[-2:]:
            d3 = F.interpolate(d3, size=e3.shape[-2:], mode="bilinear", align_corners=False)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        if d2.shape[-2:] != e2.shape[-2:]:
            d2 = F.interpolate(d2, size=e2.shape[-2:], mode="bilinear", align_corners=False)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        if d1.shape[-2:] != e1.shape[-2:]:
            d1 = F.interpolate(d1, size=e1.shape[-2:], mode="bilinear", align_corners=False)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        return self.outc(d1)


def open_gray(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("L"), dtype=np.float32)


def normalize01(x: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(x, 1), np.percentile(x, 99)
    if hi <= lo:
        hi = lo + 1.0
    x = (x - lo) / (hi - lo)
    return np.clip(x, 0.0, 1.0)


@torch.no_grad()
def predict_full(model, img01: np.ndarray, tile=512, overlap=64, device="cuda"):
    if overlap >= tile:
        raise ValueError("overlap doit être strictement inférieur à tile")

    H, W = img01.shape
    step = tile - overlap

    out = np.zeros((H, W), dtype=np.float32)
    wgt = np.zeros((H, W), dtype=np.float32)

    wy = np.hanning(tile)
    wx = np.hanning(tile)
    win = np.outer(wy, wx).astype(np.float32)
    win = (win + 1e-6) / (win.max() + 1e-6)

    for y in range(0, H, step):
        for x in range(0, W, step):
            y0 = min(y, max(0, H - tile)) if H >= tile else 0
            x0 = min(x, max(0, W - tile)) if W >= tile else 0

            patch = img01[y0:y0 + tile, x0:x0 + tile]
            if patch.shape != (tile, tile):
                pad_h = tile - patch.shape[0]
                pad_w = tile - patch.shape[1]
                patch = np.pad(patch, ((0, pad_h), (0, pad_w)), mode="reflect")

            t = torch.from_numpy(patch[None, None, ...]).float().to(device)
            prob = torch.sigmoid(model(t))[0, 0].detach().cpu().numpy().astype(np.float32)

            hh = min(tile, H - y0)
            ww = min(tile, W - x0)
            prob = prob[:hh, :ww]
            w = win[:hh, :ww]

            out[y0:y0 + hh, x0:x0 + ww] += prob * w
            wgt[y0:y0 + hh, x0:x0 + ww] += w

    return out / (wgt + 1e-7)


def main():
    parser = argparse.ArgumentParser(description="Process one image and save inferred binary mask.")
    parser.add_argument("--input", required=True, type=str, help="Input image path")
    parser.add_argument("--output", required=True, type=str, help="Output mask path (.png/.tif)")
    parser.add_argument("--checkpoint", default="runs/unet_stomata_ddp/best.pt", type=str,
                        help="Checkpoint path (default: runs/unet_stomata_ddp/best.pt)")
    parser.add_argument("--tile", default=512, type=int)
    parser.add_argument("--overlap", default=64, type=int)
    parser.add_argument("--threshold", default=0.5, type=float)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = (root / input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input introuvable: {input_path}")

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (root / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ckpt_path = Path(args.checkpoint)
    if not ckpt_path.is_absolute():
        ckpt_path = (root / ckpt_path).resolve()
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint introuvable: {ckpt_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Checkpoint: {ckpt_path}")

    ckpt = torch.load(ckpt_path, map_location="cpu")
    model = UNetSmall(1, 1, base=32).to(device)
    model.load_state_dict(ckpt["model"], strict=True)
    model.eval()

    img = normalize01(open_gray(input_path))
    prob = predict_full(model, img, tile=args.tile, overlap=args.overlap, device=device)
    pred = (prob >= float(args.threshold)).astype(np.uint8) * 255

    Image.fromarray(pred).save(output_path)
    print(f"Saved mask: {output_path}")


if __name__ == "__main__":
    main()
