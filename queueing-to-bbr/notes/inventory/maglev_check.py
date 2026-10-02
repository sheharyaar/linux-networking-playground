import random, sys
def perm(offset, skip, M): return [(offset + j*skip) % M for j in range(M)]
def populate(perms, M):
    N=len(perms); nxt=[0]*N; entry=[-1]*M; n=0
    while True:
        for i in range(N):
            c=perms[i][nxt[i]]
            while entry[c]>=0:
                nxt[i]+=1; c=perms[i][nxt[i]]
            entry[c]=i; nxt[i]+=1; n+=1
            if n==M: return entry
# Paper Table 1
M=7; os_=[(3,4),(0,2),(3,1)]
P=[perm(o,s,M) for o,s in os_]
print("perms", P)
before=populate(P,M); print("before", ['B%d'%x for x in before])
after=populate([P[0],P[2]],M); print("after ", ['B%d'%[0,2][x] for x in after])
# Figure 12 style: N=1000, remove k%, M in {65537, 655373}
random.seed(1)
def disruption(M, N, k, trials):
    tot=0
    for t in range(trials):
        names=[(random.randrange(M), random.randrange(M-1)+1) for _ in range(N)]
        P=[perm(o,s,M) for o,s in names]
        e0=populate(P,M)
        dead=set(random.sample(range(N),k))
        alive=[i for i in range(N) if i not in dead]
        e1=populate([P[i] for i in alive],M)
        e1=[alive[x] for x in e1]
        tot+=sum(1 for a,b in zip(e0,e1) if a!=b and a not in dead)/M
    return 100*tot/trials
M=int(sys.argv[1]) if len(sys.argv)>1 else 65537
for k in (5,10,20):
    print(M, "fail%%=%.1f"%(k/10), "non-failed-backend changes %% of table = %.2f"%disruption(M,1000,k,2))
