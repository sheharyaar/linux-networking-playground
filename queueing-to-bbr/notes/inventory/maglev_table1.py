def perm(o,s,M): return [(o+j*s)%M for j in range(M)]
def populate(P,M):
    N=len(P); nxt=[0]*N; e=[-1]*M; n=0; probes=0
    while True:
        for i in range(N):
            c=P[i][nxt[i]]; probes+=1
            while e[c]>=0: nxt[i]+=1; c=P[i][nxt[i]]; probes+=1
            e[c]=i; nxt[i]+=1; n+=1
            if n==M: return e, probes
M=7; names=['B0','B1','B2']; os_=[(3,4),(0,2),(3,1)]
P=[perm(o,s,M) for o,s in os_]
full,pr=populate(P,M); full=[names[x] for x in full]; print("full",full,"probes",pr)
for d in range(3):
    keep=[i for i in range(3) if i!=d]
    e,_=populate([P[i] for i in keep],M); e=[names[keep[x]] for x in e]
    extra=[r for r in range(M) if full[r]!=names[d] and full[r]!=e[r]]
    print("remove",names[d],e,"extra-disrupted rows",extra)
# add a backend B3 with (offset,skip)=(1,3)
e,_=populate(P+[perm(1,3,M)],M); print("add B3(1,3)",[(names+['B3'])[x] for x in e])
print("M=8 skip=2 from 0:", perm(0,2,8), " skip=4:", perm(0,4,8))
import math; print("E[probes] M=7:", sum(7/k for k in range(1,8)), " M=65537:", 65537*sum(1/k for k in range(1,65538)))
