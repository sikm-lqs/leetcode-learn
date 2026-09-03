import math
import torch
import torch.nn as nn

class SelfAttention(nn.Module):
    def __init__(self, d_model):
        super().__init__()

        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)

    def forward(self, x, mask=None):
        # x:[bs, seq_len, d_model]

        Q = self.w_q(x)
        K = self.w_k(x)
        V = self.w_v(x)

        scores = Q @ K.transpose(-2, -1) # [bs, seq_len, seq_len]

        d_k = Q.size(-1)
        scores = scores / math.sqrt(d_k)

        # 掩码可选
        if mask is not None:
            scores = scores.masked_fill(mask==0, float("-inf"))

        attention_weights = torch.softmax(scores, dim=-1)

        output = attention_weights @ V

        return output, attention_weights
