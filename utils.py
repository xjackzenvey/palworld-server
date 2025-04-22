import zipfile
import os

def compress_folder(folder_path: str, output_path: str):
    """
    压缩文件夹为 zip 文件
    :param folder_path: 要压缩的文件夹路径
    :param output_path: 输出的 zip 文件路径
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=folder_path)
                zipf.write(file_path, arcname)


def decompress_zip(zip_path: str, extract_to: str):
    """
    解压 zip 文件到指定目录
    :param zip_path: 要解压的 zip 文件路径
    :param extract_to: 解压到的目录
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)