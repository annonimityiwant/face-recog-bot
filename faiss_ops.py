import faiss
import numpy as np
from scipy.spatial.distance import cosine
from numpy.linalg import norm

def compute_sim( feat1, feat2):

    feat1 = feat1.ravel()
    feat2 = feat2.ravel()
    sim = np.dot(feat1, feat2) / (norm(feat1) * norm(feat2))
    return sim
d=512
k = 4

def create_index(d=512):
    index = faiss.IndexFlatIP(d)  # build the index
    return index

def  load_index(path):
    index = faiss.read_index(path)
    return index

def save_index(index:faiss.IndexFlatIP,path):
    faiss.write_index(index, path)

def add_2_indx(index:faiss.IndexFlatIP,inp_vector):
    index.add(np.expand_dims(inp_vector,0))
    return index.ntotal-1

def delete_from_index(index:faiss.IndexFlatIP,id):
    index.remove_ids(np.array([id]).astype('int64'))

def search(index,vec,k=5):
    D, I = index.search(np.expand_dims(vec,0), k)
    similarities=[]
    vecs=[]
    if len(I)>0:
        for i in I[0]:
            ret_vec=index.reconstruct(int(i))
            similarities.append(compute_sim(vec,ret_vec))

        return I[0],D[0],vecs,similarities
    else:
        return [],[],[],[]



