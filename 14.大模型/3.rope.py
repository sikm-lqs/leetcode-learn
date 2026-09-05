import torch
import math


def build_rope_cache(seq_len, d_model, base=10000):
    """
    生成 RoPE 需要的 cos / sin 表。

    输入:
        seq_len: token 数量
        d_model: 每个 token 的向量维度，必须是偶数

    输出:
        cos.shape = [seq_len, d_model // 2]
        sin.shape = [seq_len, d_model // 2]
    """

    assert d_model % 2 == 0

    # 1. 一共有多少个二维旋转平面
    num_pairs = d_model // 2

    # 2. 给每一对维度一个不同频率
    # pair_id = [0, 1, 2, ...]
    pair_id = torch.arange(num_pairs)

    freq = 1.0 / (base ** (2 * pair_id / d_model))

    print("freq:")
    print(freq)
    print("freq.shape =", freq.shape)

    # 3. 每个 token 的位置
    # pos = [0, 1, 2, ..., seq_len-1]
    pos = torch.arange(seq_len)

    print("\npos:")
    print(pos)
    print("pos.shape =", pos.shape)

    # 4. 每个位置 × 每个频率
    #
    # theta[pos, pair] = pos * freq[pair]
    theta = pos[:, None] * freq[None, :]

    print("\ntheta:")
    print(theta)
    print("theta.shape =", theta.shape)

    # 5. 二维旋转需要 cos(theta), sin(theta)
    cos = torch.cos(theta)
    sin = torch.sin(theta)

    return cos, sin


def apply_rope(x, cos, sin):
    """
    对 x 应用 RoPE。

    输入:
        x.shape = [seq_len, d_model]

    我们把最后一维两两配对：

        [x0, x1, x2, x3, ...]

    看成：

        (x0, x1)
        (x2, x3)
        ...

    每一对做二维旋转。
    """

    seq_len, d_model = x.shape

    assert d_model % 2 == 0

    # 1. 拆成二维 pair
    #
    # [seq_len, d_model]
    # ->
    # [seq_len, d_model//2, 2]
    x_pairs = x.reshape(seq_len, d_model // 2, 2)

    print("\nx_pairs:")
    print(x_pairs)
    print("x_pairs.shape =", x_pairs.shape)

    # 每一对:
    # (x, y)
    x1 = x_pairs[..., 0]
    x2 = x_pairs[..., 1]

    # x1.shape = [seq_len, d_model//2]
    # x2.shape = [seq_len, d_model//2]

    # 2. 标准二维旋转公式
    #
    # x' = x cosθ - y sinθ
    # y' = x sinθ + y cosθ

    y1 = x1 * cos - x2 * sin
    y2 = x1 * sin + x2 * cos

    # 3. 拼回来
    y_pairs = torch.stack([y1, y2], dim=-1)

    # [seq_len, d_model//2, 2]
    # ->
    # [seq_len, d_model]
    y = y_pairs.reshape(seq_len, d_model)

    return y


seq_len = 4
d_model = 4

q = torch.tensor([
    [1.0, 0.0, 1.0, 0.0],   # token 0
    [1.0, 0.0, 1.0, 0.0],   # token 1
    [1.0, 0.0, 1.0, 0.0],   # token 2
    [1.0, 0.0, 1.0, 0.0],   # token 3
])

print("原始 q:")
print(q)
print("q.shape =", q.shape)

cos, sin = build_rope_cache(
    seq_len=seq_len,
    d_model=d_model
)

q_rope = apply_rope(q, cos, sin)

print("\nRoPE 后:")
print(q_rope)
print("q_rope.shape =", q_rope.shape)