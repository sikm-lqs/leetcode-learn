import math
import torch
import torch.nn as nn

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()

        assert d_model % num_heads == 0

        self.d_model = d_model
        self.num_heads = num_heads

        self.head_dim = d_model // num_heads

        self.w_q = nn.Linear(d_model, d_model)
        self.w_k = nn.Linear(d_model, d_model)
        self.w_v = nn.Linear(d_model, d_model)

        self.w_o = nn.Linear(d_model, d_model)

    def forward(self, x, mask = None):
        # x:[bs, seq_len, d_model]

        bs, seq_len, d = x.shape

        Q = self.w_q(x) # bs, seq_len, d
        K = self.w_k(x)
        V = self.w_v(x)

        Q = Q.view(bs, seq_len, self.num_heads, self.head_dim)
        K = K.view(bs, seq_len, self.num_heads, self.head_dim)
        V = V.view(bs, seq_len, self.num_heads, self.head_dim)

        Q = Q.transpose(1, 2) # bs, num_heads, seq_len, head_dim
        K = K.transpose(1, 2)
        V = V.transpose(1, 2)

        scores = Q @ K.transpose(-2, -1) # bs, num_heads, seq_len, seq_len

        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))

        attention_weights = torch.softmax(scores, dim=-1)

        attention_output = attention_weights @ V

        attention_output = attention_output.transpose(1, 2)
        attention_output = attention_output.contiguous()

        attention_output = attention_output.view(bs, seq_len, d)

        output = self.w_o(attention_output)

        return output, attention_weights
