from PIL import Image
import os
import glob


def overlay_mask_on_image(image_path, mask_path, output_path, alpha=0.5):
    image = Image.open(image_path)
    mask = Image.open(mask_path).convert("RGB")
    overlay = Image.blend(image, mask, alpha)
    if output_path.endswith('.jpg') or output_path.endswith('.jpeg'):
        overlay = overlay.convert("RGB")  # 去除透明度
        overlay.save(output_path, "JPEG")
    else:
        overlay.save(output_path, "PNG")


def process_directory(image_dir, mask_dir, output_dir, alpha=0.5):
    os.makedirs(output_dir, exist_ok=True)
    image_files = glob.glob(os.path.join(image_dir, "*.jpg"))

    for image_file in image_files:
        base_name = os.path.splitext(os.path.basename(image_file))[0]
        mask_file = os.path.join(mask_dir, base_name + "_mask.png")
        output_file = os.path.join(output_dir, base_name + '.png')

        if os.path.exists(mask_file):
            overlay_mask_on_image(image_file, mask_file, output_file, alpha)
            print(f"Processed: {image_file} with {mask_file}")
        else:
            print(f"Mask not found for {image_file}")


if __name__ == '__main__':
    image_directory = '../test'  # 输入图片所在目录，包含原图和mask
    mask_directory = '../run/road/deeplab-xception/experiment_1/result'
    output_directory = '../run/road/deeplab-xception/experiment_1/overlay'  # 叠加结果保存目录
    process_directory(image_directory, mask_directory, output_directory, alpha=0.4)
