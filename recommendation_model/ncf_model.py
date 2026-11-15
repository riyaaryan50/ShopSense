
import torch
import torch.nn as nn


class NeuMF(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim=32):
        super().__init__()

        # GMF branch
        self.gmf_user = nn.Embedding(num_users, embedding_dim)
        self.gmf_item = nn.Embedding(num_items, embedding_dim)

        # MLP branch
        self.mlp_user = nn.Embedding(num_users, embedding_dim)
        self.mlp_item = nn.Embedding(num_items, embedding_dim)

        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim * 2, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU()
        )

        # Final prediction layer
        self.output = nn.Linear(embedding_dim + 16, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, user_ids, item_ids):
        # GMF calculation
        gmf_u = self.gmf_user(user_ids)
        gmf_i = self.gmf_item(item_ids)
        gmf_out = gmf_u * gmf_i

        # MLP calculation
        mlp_u = self.mlp_user(user_ids)
        mlp_i = self.mlp_item(item_ids)

        mlp_input = torch.cat([mlp_u, mlp_i], dim=1)
        mlp_out = self.mlp(mlp_input)

        # Combine GMF and MLP
        combined = torch.cat([gmf_out, mlp_out], dim=1)

        prediction = self.sigmoid(self.output(combined))

        return prediction.squeeze(1)
