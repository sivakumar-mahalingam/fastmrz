"""Export the trained network to ONNX (BatchNorm folded, softmax excluded)."""
import sys, torch, numpy as np
from train import Net, H, W  # noqa: run from the tools directory
net = Net(); net.load_state_dict(torch.load(sys.argv[1], map_location="cpu")); net.eval()
x = torch.rand(1, 1, H, W)
torch.onnx.export(net, x, sys.argv[2], input_names=["image"], output_names=["logits"], opset_version=13,
                  dynamic_axes={"image": {0: "n"}, "logits": {0: "n"}}, do_constant_folding=True, dynamo=False)
import cv2, onnxruntime as ort
xb = torch.rand(5, 1, H, W)
ref = net(xb).detach().numpy()
o = ort.InferenceSession(sys.argv[2]).run(None, {"image": xb.numpy()})[0]
n = cv2.dnn.readNetFromONNX(sys.argv[2]); n.setInput(xb.numpy()); c = n.forward()
print("ort diff", abs(o - ref).max(), "cv2 diff", abs(c - ref).max(), c.shape)
