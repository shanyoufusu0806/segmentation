import argparse
import os
import numpy as np
import time

from modeling.deeplab import *
from dataloaders import custom_transforms as tr
from PIL import Image
from torchvision import transforms
from dataloaders.utils import *
from torchvision.utils import make_grid, save_image


def main():
    parser = argparse.ArgumentParser(description="PyTorch DeeplabV3Plus Training")
    parser.add_argument('--in-path', type=str, required=True, help='image to test')
    parser.add_argument('--out-path', type=str, default='result', required=True, help='mask image to save')
    parser.add_argument('--backbone', type=str, default='resnet',
                        choices=['resnet', 'xception', 'drn', 'mobilenet'],
                        help='backbone name (default: resnet)')
    parser.add_argument('--ckpt', type=str, default='deeplab-resnet.pth', help='saved model')
    parser.add_argument('--out-stride', type=int, default=16,
                        help='network output stride (default: 8)')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA training')
    parser.add_argument('--gpu-ids', type=str, default='0',
                        help='use which gpu to train, must be a \
                        comma-separated list of integers only (default=0)')
    parser.add_argument('--dataset', type=str, default='road',
                        choices=['pascal', 'coco', 'cityscapes', 'road'],
                        help='dataset name (default: pascal)')
    parser.add_argument('--crop-size', type=int, default=720,
                        help='crop image size')
    parser.add_argument('--num_classes', type=int, default=2,
                        help='crop image size')
    parser.add_argument('--sync-bn', type=bool, default=None,
                        help='whether to use sync bn (default: auto)')
    parser.add_argument('--freeze-bn', type=bool, default=False,
                        help='whether to freeze bn parameters (default: False)')

    args = parser.parse_args()
    args.cuda = not args.no_cuda and torch.cuda.is_available()
    if args.cuda:
        try:
            args.gpu_ids = [int(s) for s in args.gpu_ids.split(',')]
        except ValueError:
            raise ValueError('Argument --gpu_ids must be a comma-separated list of integers only')

    if args.sync_bn is None:
        if args.cuda and len(args.gpu_ids) > 1:
            args.sync_bn = True
        else:
            args.sync_bn = False
    model_s_time = time.time()
    model = DeepLab(num_classes=args.num_classes,
                    backbone=args.backbone,
                    output_stride=args.out_stride,
                    sync_bn=args.sync_bn,
                    freeze_bn=args.freeze_bn)

    ckpt = torch.load(args.ckpt, map_location='cpu')
    model.load_state_dict(ckpt['state_dict'])
    model = model.cuda()

    total = sum([param.nelement() for param in model.parameters()])
    # 精确地计算：1MB=1024KB=1048576字节
    print('Number of parameter: % .4fM' % (total / 1e6))

    model_u_time = time.time()
    model_load_time = model_u_time - model_s_time
    print("model load time is {}".format(model_load_time))

    composed_transforms = transforms.Compose([
        tr.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        tr.ToTensor()])
    for name in os.listdir(args.in_path):
        s_time = time.time()
        image = Image.open(args.in_path + "/" + name).convert('RGB')

        # image = Image.open(args.in_path).convert('RGB')
        target = Image.open(args.in_path + "/" + name).convert('L')
        sample = {'image': image, 'label': target}
        tensor_in = composed_transforms(sample)['image'].unsqueeze(0)

        model.eval()
        if args.cuda:
            tensor_in = tensor_in.cuda()
        with torch.no_grad():
            output = model(tensor_in)

        grid_image = make_grid(decode_seg_map_sequence(torch.max(output[:3], 1)[1].detach().cpu().numpy(), args.dataset),
                               3, normalize=False, value_range=(0, 255))
        os.makedirs(args.out_path, exist_ok=True)
        save_image(grid_image, args.out_path + "/" + "{}_mask.png".format(name[0:-4]))
        u_time = time.time()
        img_time = u_time - s_time
        print("image:{} time: {} ".format(name, img_time))
        # save_image(grid_image, args.out_path)
        # print("type(grid) is: ", type(grid_image))
        # print("grid_image.shape is: ", grid_image.shape)
    print("image save in out_path.")


if __name__ == "__main__":
    main()

# python demo.py --in-path your_file --out-path your_dst_file
