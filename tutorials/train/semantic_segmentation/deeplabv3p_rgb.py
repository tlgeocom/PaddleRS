#!/usr/bin/env python

# 图像分割模型DeepLab V3+训练示例脚本，用来处理三波段RGB影像
# 执行此脚本前，请确认已正确安装PaddleRS库

import paddlers as pdrs
from paddlers import transforms as T

# 数据集存放目录
DATA_DIR = './data/rsseg_rgb/'
# 训练集`file_list`文件路径
TRAIN_FILE_LIST_PATH = './data/rsseg_rgb/train.txt'
# 验证集`file_list`文件路径
EVAL_FILE_LIST_PATH = './data/rsseg_rgb/val.txt'
# 数据集类别信息文件路径
LABEL_LIST_PATH = './data/rsseg_rgb/labels.txt'
# 实验目录，保存输出的模型权重和结果
EXP_DIR = './output/deeplabv3p_rgb/'

# 影像波段数量
NUM_BANDS = 3

# 下载和解压多光谱地块分类数据集
#pdrs.utils.download_and_decompress(
#    'https://paddlers.bj.bcebos.com/datasets/rsseg_rgb.zip', path='./data/')

# 定义训练和验证时使用的数据变换（数据增强、预处理等）
# 使用Compose组合多种变换方式。Compose中包含的变换将按顺序串行执行
# API说明：https://github.com/PaddlePaddle/PaddleRS/blob/develop/docs/apis/data.md
train_transforms = T.Compose([
    # 读取影像
    T.DecodeImg(),
    # 将影像缩放到512x512大小
    T.Resize(target_size=512),
    # 以50%的概率实施随机水平翻转
    T.RandomHorizontalFlip(prob=0.5),
    # 将数据归一化到[-1,1]
    T.Normalize(
        mean=[0.5] * NUM_BANDS, std=[0.5] * NUM_BANDS),
    T.ArrangeSegmenter('train')
])

eval_transforms = T.Compose([
    T.DecodeImg(),
    T.Resize(target_size=512),
    # 验证阶段与训练阶段的数据归一化方式必须相同
    T.Normalize(
        mean=[0.5] * NUM_BANDS, std=[0.5] * NUM_BANDS),
    T.ReloadMask(),
    T.ArrangeSegmenter('eval')
])

# 分别构建训练和验证所用的数据集
train_dataset = pdrs.datasets.SegDataset(
    data_dir=DATA_DIR,
    file_list=TRAIN_FILE_LIST_PATH,
    label_list=LABEL_LIST_PATH,
    transforms=train_transforms,
    num_workers=0,
    shuffle=True)

eval_dataset = pdrs.datasets.SegDataset(
    data_dir=DATA_DIR,
    file_list=EVAL_FILE_LIST_PATH,
    label_list=LABEL_LIST_PATH,
    transforms=eval_transforms,
    num_workers=0,
    shuffle=False)

# 构建DeepLab V3+模型，使用ResNet-50作为backbone
# 目前已支持的模型请参考：https://github.com/PaddlePaddle/PaddleRS/blob/develop/docs/intro/model_zoo.md
# 模型输入参数请参考：https://github.com/PaddlePaddle/PaddleRS/blob/develop/paddlers/tasks/segmenter.py
model = pdrs.tasks.seg.DeepLabV3P(
    in_channels=NUM_BANDS,
    num_classes=len(train_dataset.labels),
    backbone='ResNet50_vd')

# 执行模型训练
model.train(
    num_epochs=10,
    train_dataset=train_dataset,
    train_batch_size=2,
    eval_dataset=eval_dataset,
    save_interval_epochs=5,
    # 每多少次迭代记录一次日志
    log_interval_steps=4,
    save_dir=EXP_DIR,
    # 初始学习率大小
    learning_rate=0.001,
    # 是否使用early stopping策略，当精度不再改善时提前终止训练
    early_stop=False,
    # 是否启用VisualDL日志功能
    use_vdl=True,
    # 指定从某个检查点继续训练
    resume_checkpoint=None)
