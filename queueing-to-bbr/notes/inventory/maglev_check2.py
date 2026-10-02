import random, sys
def populate(os_, M):
    N=len(os_); nxt=[0]*N; entry=[-1]*M; n=0
    off=[o for o,s in os_]; sk=[s for o,s in os_]
    while True:
        for i in range(N):
            c=(off[i]+nxt[i]*sk[i])%M
            while entry[c]>=0:
                nxt[i]+=1; c=(off[i]+nxt[i]*sk[i])%M
            entry[c]=i; nxt[i]+=1; n+=1
            if n==M: return entry
random.seed(2)
def run(M,N,k,trials):
    a=b=0
    for t in range(trials):
        os_=[(random.randrange(M), random.randrange(M-1)+1) for _ in range(N)]
        e0=populate(os_,M)
        dead=set(random.sample(range(N),k)); alive=[i for i in range(N) if i not in dead]
        e1=[alive[x] for x in populate([os_[i] for i in alive],M)]
        a+=sum(1 for x,y in zip(e0,e1) if x!=y and x not in dead)/M
        b+=sum(1 for x,y in zip(e0,e1) if x!=y)/M
        cnt=[0]*N
        for x in e0: cnt[x]+=1
    return 100*a/trials, 100*b/trials, min(cnt), max(cnt)
M=int(sys.argv[1]); ks=[int(x) for x in sys.argv[2:]]
for k in ks:
    r=run(M,1000,k,1)
    print(f"M={M} N=1000 k={k} ({k/10:.1f}%): extra={r[0]:.2f}% total={r[1]:.2f}% entries/backend min={r[2]} max={r[3]}")
