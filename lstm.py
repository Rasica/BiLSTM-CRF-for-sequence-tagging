import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

torch.manual_seed(1)


class LSTMTagger(nn.Module):

    def __init__(self, embedding_dim, hidden_dim, vocab_size, tagset_size, pretrained_weight_embeddings, USE_CRF=False,
                 BIDIRECTIONAL=False, USE_BIGRAM=False, bigram_size=0, USE_SPELLING=False, SPELLING_SIZE=7):
        super(LSTMTagger, self).__init__()
        self.tagset_size = tagset_size
        self.hidden_dim = hidden_dim
        self.word_embeddings = nn.Embedding(vocab_size, embedding_dim)
        # self.word_embeddings.weight.requires_grad = False
        # print("Entered!!!!")
        # if pretrained_weight_embeddings != None:
        self.bidirectional = BIDIRECTIONAL
        self.word_embeddings.weight.data.copy_(torch.from_numpy(pretrained_weight_embeddings))
        if BIDIRECTIONAL:
            self.lstm = nn.LSTM(embedding_dim, hidden_dim // 2, bidirectional=BIDIRECTIONAL)
        else:
            self.lstm = nn.LSTM(embedding_dim, hidden_dim)


        self.use_bigram = USE_BIGRAM
        self.use_spelling = USE_SPELLING
        self.hidden = self.init_hidden()
        self.hidden2tag = nn.Linear(
            (hidden_dim // 2 if self.bidirectional else hidden_dim) + (bigram_size if self.use_bigram else 0) + (SPELLING_SIZE if self.use_spelling else 0),
            tagset_size)  # this means, given embedding dimension 300 and bigram feature dimension 20, the input dimension to FC layer is 320.

    def init_hidden(self):
        if not self.bidirectional:
            return (autograd.Variable(torch.randn(1, 1, self.hidden_dim)),
                    autograd.Variable(torch.randn(1, 1, self.hidden_dim)))
        else:
            return (autograd.Variable(torch.randn(2, 1, self.hidden_dim // 2)),
                    autograd.Variable(torch.randn(2, 1, self.hidden_dim // 2)))

    def forward(self, sentence, bigram_one_hot=None, spelling_one_hot=None):
        embeds = self.word_embeddings(sentence)  # shape seq_length * emb_size
        # print(embeds.view(len(sentence), 1, -1).shape)
        lstm_out, self.hidden = self.lstm(
            embeds.view(len(sentence), 1, -1), self.hidden)
        # print("original shape before MLP "+str(lstm_out.view(len(sentence), -1).shape))
        # print("shape of onehot bigram "+str(bigram_one_hot.shape))

        # if self.use_bigram:
        # print("concatednated vector"+str(torch.cat([lstm_out.view(len(sentence), -1),bigram_one_hot],dim=1).shape))

        # print([lstm_out.view(len(sentence), -1)] + ([bigram_one_hot] if self.use_bigram else []) + (
        #         [spelling_one_hot] if self.use_spelling else []))
        tag_space = self.hidden2tag(torch.cat(
            [lstm_out.view(len(sentence), -1)] + ([bigram_one_hot] if self.use_bigram else []) + (
                [spelling_one_hot] if self.use_spelling else []), dim=1))
        # else:
        #     tag_space = self.hidden2tag(lstm_out.view(len(sentence), -1))

        tag_scores = F.log_softmax(tag_space, dim=1)

        # print("calculating forwarding "+str(self.use_bigram))
        return tag_scores
